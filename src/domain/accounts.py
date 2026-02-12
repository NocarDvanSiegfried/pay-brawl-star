from dataclasses import dataclass


@dataclass
class BrawlStarsAccount:
    email: str


@dataclass
class GoogleAccount:
    email: str
    password: str
    backup_code: str
