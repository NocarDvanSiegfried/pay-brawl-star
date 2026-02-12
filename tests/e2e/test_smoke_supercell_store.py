import re

from playwright.sync_api import Page, expect


def test_supercell_store_smoke(page: Page) -> None:
    """Smoke-тест доступности магазина Brawl Stars на Supercell Store.

    Использует встроенную фикстуру `page` из pytest-playwright.
    """
    page.goto("https://store.supercell.com/brawlstars")

    # Проверяем, что заголовок страницы относится к Brawl Stars Store.
    expect(page).to_have_title(re.compile("Brawl Stars", re.IGNORECASE))

    # Дополнительная проверка: на странице есть заголовок с текстом "Discover Brawl Stars Store" или похожим.
    heading = page.get_by_role("heading", name=re.compile("Brawl Stars", re.IGNORECASE))
    expect(heading).to_be_visible()
