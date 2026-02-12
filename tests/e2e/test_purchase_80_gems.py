import re

from playwright.sync_api import Page, expect

from src.application.flows.login_supercell import login_supercell_with_manual_otp
from src.application.flows.purchase_80_gems_flow import purchase_80_gems_flow
from src.infrastructure.config.settings import Settings


def test_purchase_80_gems_end_to_end(page: Page, settings: Settings) -> None:
    """Полный e2e-сценарий: логин в Supercell + покупка 80 гемов через Google Pay.

    Проверяем, что после завершения потока пользователь разлогинен (видна кнопка Log in).
    Логика шагов инкапсулирована во flow-ах application-слоя.
    """

    # 1. Логин по email + ручной ввод ОТП.
    login_supercell_with_manual_otp(page, settings)

    # 2. Покупка 80 гемов + оплата Google Pay + best-effort финализация сессии.
    purchase_80_gems_flow(page, settings)

    # 3. Проверяем, что мы вернулись на страницу магазина и видим кнопку входа.
    page.goto("https://store.supercell.com/brawlstars")
    login_button = page.get_by_role(
        "link",
        name=re.compile("Log in|Войти", re.IGNORECASE),
    )
    expect(login_button).to_be_visible()
