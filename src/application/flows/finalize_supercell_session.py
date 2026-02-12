from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from playwright.sync_api import Page

from src.infrastructure.browser.supercell_store_client import SupercellStoreClient


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _load_supercell_config() -> Dict[str, Any]:
    config_path = PROJECT_ROOT / "config.yaml"
    with config_path.open(encoding="utf-8") as f:
        raw: Dict[str, Any] = yaml.safe_load(f)
    return raw.get("supercell", {})


def finalize_supercell_session(page: Page) -> None:
    """Финализирует сессию Supercell: отвязка способа оплаты и логаут.

    Best-effort: если какие-то шаги не удаётся выполнить (например, уже отвязано
    или пользователь разлогинен), мы не роняем весь сценарий, а продолжаем.
    """

    cfg = _load_supercell_config()
    base_url: str = cfg.get("base_url", "https://store.supercell.com")
    game_slug: str = cfg.get("game_slug", "brawlstars")
    account_url: Optional[str] = cfg.get("account_url")

    client = SupercellStoreClient(page=page, base_url=base_url, game_slug=game_slug)

    try:
        client.open_account_page(account_url=account_url)
    except Exception:
        # Если не удалось открыть страницу аккаунта, дальше смысла продолжать нет.
        return

    try:
        client.detach_payment_method()
    except Exception:
        # Не критично: возможно, метода оплаты уже нет или DOM изменился.
        pass

    try:
        client.logout_supercell()
    except Exception:
        # Если не удалось явно разлогиниться, просто выходим.
        pass
