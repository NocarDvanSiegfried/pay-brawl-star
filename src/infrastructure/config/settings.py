from dataclasses import dataclass
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


# Загружаем .env из корня репозитория
PROJECT_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass
class Settings:
    """Глобальные настройки проекта, загружаемые из окружения/конфигов.

    Секреты (логины/пароли/backup-коды, прокси) берём из .env, остальные параметры
    могут быть заданы в коде или отдельном не-секретном конфиге.
    """

    # Supercell / Brawl Stars
    brawl_email: str

    # Google / Google Pay
    google_email: str
    google_password: str
    google_backup_code: str

    # Proxy (опционально)
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None

    # Режим получения ОТП: manual | email (пока используется manual)
    otp_mode: str = "manual"


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required environment variable {name} is not set")
    return value


def load_settings() -> Settings:
    """Загружает настройки из переменных окружения.

    Использует .env (через python-dotenv) и жёстко требует наличия критичных полей,
    чтобы как можно раньше упасть с понятной ошибкой.
    """

    return Settings(
        brawl_email=_require("BS_EMAIL"),
        google_email=_require("GOOGLE_EMAIL"),
        google_password=_require("GOOGLE_PASSWORD"),
        google_backup_code=_require("GOOGLE_BACKUP_CODE"),
        http_proxy=os.environ.get("HTTP_PROXY") or None,
        https_proxy=os.environ.get("HTTPS_PROXY") or None,
        otp_mode=os.environ.get("OTP_MODE", "manual"),
    )
