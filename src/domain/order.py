from dataclasses import dataclass


@dataclass
class Order:
    sku_name: str
    quantity: int = 1
