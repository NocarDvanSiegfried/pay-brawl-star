import os
from pathlib import Path
from typing import Dict

import pytest
from playwright.sync_api import BrowserContext, Page
from playwright.sync_api import expect as playwright_expect

from src.infrastructure.config.settings import load_settings
from src.infrastructure.logging.events import log_event


ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="session")
def settings():
    """Глобальные настройки сценария, загружаемые один раз за сессию тестов."""

    return load_settings()


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: Dict, settings) -> Dict:
    """Дополняем опции браузерного контекста прокси и базовыми настройками.

    По аналогии с Nx-конфигами runner'а, здесь храним все e2e-настройки окружения,
    а доменный код об этом ничего не знает.
    """

    proxy_server = settings.http_proxy or settings.https_proxy

    extra: Dict = {**browser_context_args}
    if proxy_server:
        extra["proxy"] = {"server": proxy_server}

    # Включаем запись видео на уровне контекста, чтобы при падении иметь артефакты.
    extra.setdefault("record_video_dir", str(ARTIFACTS_DIR / "video"))

    return extra


@pytest.fixture(autouse=True)
def _configure_timeouts(context: BrowserContext) -> None:
    """Глобально настраиваем таймауты для всех тестов.

    Используем значения по умолчанию; при необходимости можно связать с config.yaml.
    """

    # 30 cекунд на любые действия и 45 секунд на навигацию
    context.set_default_timeout(30_000)
    context.set_default_navigation_timeout(45_000)


@pytest.fixture(autouse=True)
def _configure_expect_timeout() -> None:
    """Настраиваем глобальный таймаут для expect-assertions."""

    playwright_expect.set_options(timeout=10_000)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Хук pytest: добавляет к test item информацию об исходе для post-factum-фикстур."""

    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(autouse=True)
def _capture_artifacts_on_failure(request, page: Page) -> None:
    """Сохраняет скриншот и логирует событие при падении теста.

    Логика остаётся в слое тестов (runner), доменный код об этом не знает.
    """

    yield

    rep = getattr(request.node, "rep_call", None)
    if rep is not None and rep.failed:
        test_name = request.node.name
        screenshot_dir = ARTIFACTS_DIR / "screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = screenshot_dir / f"{test_name}.png"

        try:
            page.screenshot(path=str(screenshot_path), full_page=True)
        except Exception:
            # Если страница уже закрыта или упала раньше, просто пропускаем.
            screenshot_path = None

        log_event(
            stage="test_failure",
            status="error",
            message=f"Test {test_name} failed",
            data={"screenshot": str(screenshot_path) if screenshot_path else None},
        )
