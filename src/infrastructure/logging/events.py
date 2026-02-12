import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


LOGS_DIR = Path(__file__).resolve().parents[3] / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / "events.ndjson"


@dataclass
class Event:
    stage: str
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None


def log_event(stage: str, status: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
    """Пишет одну строку NDJSON с информацией о шаге сценария.

    Формат близкий к agent_log из reference-репозитория: timestamp + поля события.
    """

    payload = Event(stage=stage, status=status, message=message, data=data or {})
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        **asdict(payload),
    }

    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
