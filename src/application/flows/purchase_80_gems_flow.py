from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from playwright.sync_api import Page

from src.infrastructure.browser.google_pay_client import GooglePayClient
from src.infrastructure.browser.supercell_store_client import SupercellStoreClient
from src.infrastructure.config.settings import Settings
from src.application.flows.finalize_supercell_session import finalize_supercell_session


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _load_order_config() -> Dict[str, Any]:
    config_path = PROJECT_ROOT / "config.yaml"
    with config_path.open(encoding="utf-8") as f:
        raw: Dict[str, Any] = yaml.safe_load(f)
    return raw.get("order", {})


def _load_supercell_config() -> Dict[str, Any]:
    config_path = PROJECT_ROOT / "config.yaml"
    with config_path.open(encoding="utf-8") as f:
        raw: Dict[str, Any] = yaml.safe_load(f)
    return raw.get("supercell", {})


def purchase_80_gems_flow(page: Page, settings: Settings) -> None:
    """Полный этап покупки 80 гемов через Google Pay.

    Этап 4 (оплата) + Этап 5 (отвязка способа оплаты и логаут):
    - переход к товару, добавление в корзину, checkout;
    - выбор Google Pay, логин в Google и подтверждение оплаты;
    - попытка отвязать способ оплаты и выйти из аккаунта Supercell.
    """

    supercell_cfg = _load_supercell_config()
    order_cfg = _load_order_config()

    base_url: str = supercell_cfg.get("base_url", "https://store.supercell.com")
    game_slug: str = supercell_cfg.get("game_slug", "brawlstars")
    product_url: Optional[str] = order_cfg.get("product_url")

    store_client = SupercellStoreClient(page=page, base_url=base_url, game_slug=game_slug)

    try:
        # Этап 3: товар/корзина + Этап 4: оплата.
        store_client.go_to_product_80_gems(product_url=product_url)
        store_client.add_to_cart_single_quantity()

        # Выбор оплаты Google Pay должен открыть попап; оборачиваем в expect_popup.
        with page.expect_popup() as popup_info:
            # Нажимаем Checkout, после чего на странице Supercell появится шаг с выбором способа оплаты.
            store_client.proceed_to_checkout()

            # Здесь ожидаем кнопку Google Pay и жмём её.
            gpay_button = page.get_by_role(
                "button",
                name="Google Pay",
            )
            gpay_button.click()

        popup_page = popup_info.value

        # В попапе выполняем логин в Google и подтверждение оплаты.
        gpay_client = GooglePayClient(popup_page)
        gpay_client.login_and_confirm_payment(
            email=settings.google_email,
            password=settings.google_password,
            backup_code=settings.google_backup_code,
        )

    finally:
        # Этап 5: best-effort финализация (отвязка способа оплаты и логаут).
        finalize_supercell_session(page)
