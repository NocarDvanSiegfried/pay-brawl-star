from dataclasses import dataclass

from .accounts import BrawlStarsAccount, GoogleAccount
from .order import Order


@dataclass
class PurchaseSettings:
    game_slug: str
    proxy_enabled: bool = True


def purchase_80_gems(brawl_account: BrawlStarsAccount, google_account: GoogleAccount, settings: PurchaseSettings) -> Order:
    """Domain-level description: returns desired order (80 gems, qty=1).

    Инфраструктурные детали (Playwright, DOM, Google Pay) здесь не реализуются.
    """
    return Order(sku_name="80_gems", quantity=1)
