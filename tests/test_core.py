from datetime import date, datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.filters import filter_events
from app.formatter import jalali_long
from app.models import CalendarEvent
from app.timezone_utils import parse_api_datetime, to_tehran
from app.translator import Translator


def _ev(hour=12, importance=3, ccy="USD", title="CPI"):
    utc = datetime(2026, 9, 23, hour, 30, tzinfo=timezone.utc)
    return CalendarEvent("1", title, title, ccy, "US", importance, utc, to_tehran(utc), "2.5%", "2.4%", "-")


def test_timezone():
    dt = parse_api_datetime("2026-09-23T12:30:00")
    tehran = to_tehran(dt)
    assert tehran.tzinfo is not None
    assert tehran.hour in {15, 16}


def test_filter_and_sort():
    events = [_ev(14, 1, "USD"), _ev(10, 3, "EUR"), _ev(10, 3, "XYZ")]
    out = filter_events(events, date(2026, 9, 23), 2, ["USD", "EUR"])
    assert len(out) == 1
    assert out[0].currency == "EUR"


def test_translation():
    tr = Translator(ROOT / "data" / "translations.json")
    assert "غیرکشاورزی" in tr.translate("Non Farm Payrolls")
    assert tr.translate("Something Unknown XYZ") == "Something Unknown XYZ"


def test_jalali():
    label = jalali_long(date(2026, 9, 23))
    assert "۱۴۰۵" in label or "1405" in label
