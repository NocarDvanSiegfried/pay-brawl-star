from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml
from playwright.sync_api import Page

from src.infrastructure.browser.supercell_store_client import SupercellStoreClient
from src.infrastructure.config.settings import Settings


PROJECT_ROOT = Path(__file__).resolve().parents[3]


@dataclass
class SupercellConfig:
    base_url: str
    game_slug: str


def load_supercell_config() -> SupercellConfig:
    """Загружает базовые URL/slug для Supercell из config.yaml.

    Это не-секретная конфигурация, общая для всего сценария.
    """

    config_path = PROJECT_ROOT / "config.yaml"
    with config_path.open(encoding="utf-8") as f:
        raw: Dict[str, Any] = yaml.safe_load(f)

    supercell = raw.get("supercell", {})
    base_url = supercell.get("base_url", "https://store.supercell.com")
    game_slug = supercell.get("game_slug", "brawlstars")

    return SupercellConfig(base_url=base_url, game_slug=game_slug)


def login_supercell_with_manual_otp(page: Page, settings: Settings) -> None:
    """Логин в Supercell Store по email + ОТП с ручным вводом кода.

    - открывает страницу игры;
    - запускает логин по email из настроек;
    - запрашивает у пользователя ОТП-код в консоли;
    - вводит код и дожидается возврата в магазин.
    """

    cfg = load_supercell_config()
    client = SupercellStoreClient(page=page, base_url=cfg.base_url, game_slug=cfg.game_slug)

    client.start_login(settings.brawl_email)

    otp_code = input("Введите ОТП-код из письма Supercell: ").strip()
    if not otp_code:
        raise RuntimeError("ОТП-код не был введён")

    client.complete_login_with_otp(otp_code)
