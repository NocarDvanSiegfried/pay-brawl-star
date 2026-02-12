from dataclasses import dataclass
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    brawl_email: str
    google_email: str
    google_password: str
    google_backup_code: str


def load_settings() -> Settings:
    return Settings(
        brawl_email=os.environ.get("BS_EMAIL", ""),
        google_email=os.environ.get("GOOGLE_EMAIL", ""),
        google_password=os.environ.get("GOOGLE_PASSWORD", ""),
        google_backup_code=os.environ.get("GOOGLE_BACKUP_CODE", ""),
    )
