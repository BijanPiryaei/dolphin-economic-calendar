from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass
class CalendarEvent:
    event_id: str
    title: str
    title_en: str
    currency: str
    country: str
    importance: int  # 1 low, 2 medium, 3 high
    dt_utc: datetime
    dt_tehran: datetime
    forecast: str
    previous: str
    actual: str
    unit: str = ""

    def to_dict(self) -> dict:
        data = asdict(self)
        data["dt_utc"] = self.dt_utc.isoformat()
        data["dt_tehran"] = self.dt_tehran.isoformat()
        return data
