from __future__ import annotations

import json
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

from app.models import CalendarEvent
from app.timezone_utils import parse_api_datetime, to_tehran
from app.translator import Translator

COUNTRY_CCY = {
    "united states": "USD",
    "usa": "USD",
    "us": "USD",
    "euro area": "EUR",
    "eurozone": "EUR",
    "germany": "EUR",
    "france": "EUR",
    "italy": "EUR",
    "spain": "EUR",
    "united kingdom": "GBP",
    "uk": "GBP",
    "japan": "JPY",
    "canada": "CAD",
    "australia": "AUD",
    "new zealand": "NZD",
    "switzerland": "CHF",
    "china": "CNY",
}


class CalendarFetchError(Exception):
    pass


def _retry_get(url: str, params: dict, headers: dict | None = None, attempts: int = 3) -> requests.Response:
    delays = [10, 30, 60]
    last: Exception | None = None
    for i in range(attempts):
        try:
            resp = requests.get(url, params=params, headers=headers or {}, timeout=30)
            if resp.status_code >= 500:
                raise CalendarFetchError(f"HTTP {resp.status_code}")
            resp.raise_for_status()
            return resp
        except Exception as exc:  # noqa: BLE001
            last = exc
            if i < attempts - 1:
                time.sleep(delays[i])
    raise CalendarFetchError(str(last))


def _imp_te(value) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return 0
    return n if n in (1, 2, 3) else 0


def _imp_fh(value) -> int:
    mapping = {"low": 1, "medium": 2, "med": 2, "high": 3}
    return mapping.get(str(value).lower().strip(), 0)


class CalendarClient:
    def __init__(self, settings, translator: Translator, fixtures_dir: Path) -> None:
        self.settings = settings
        self.translator = translator
        self.fixtures_dir = fixtures_dir

    def fetch(self, target: date) -> list[CalendarEvent]:
        provider = self.settings.api_provider
        if provider == "trading_economics":
            return self._te(target)
        if provider == "finnhub":
            return self._finnhub(target)
        if provider == "mock":
            return self._mock(target)
        raise CalendarFetchError(f"unknown provider: {provider}")

    def _te(self, target: date) -> list[CalendarEvent]:
        key = self.settings.trading_economics_key
        if not key:
            raise CalendarFetchError("TRADING_ECONOMICS_API_KEY missing")
        start = target.isoformat()
        end = (target + timedelta(days=1)).isoformat()
        url = f"https://api.tradingeconomics.com/calendar/country/all/{start}/{end}"
        resp = _retry_get(url, {"c": key, "f": "json"})
        payload = resp.json()
        if not isinstance(payload, list):
            raise CalendarFetchError("invalid Trading Economics payload")
        events: list[CalendarEvent] = []
        for row in payload:
            try:
                events.append(self._from_te(row))
            except Exception:
                continue
        return events

    def _from_te(self, row: dict) -> CalendarEvent:
        title_en = str(row.get("Event") or row.get("Category") or "").strip()
        country = str(row.get("Country") or "").strip()
        ccy = (row.get("Currency") or COUNTRY_CCY.get(country.lower(), "")).upper()
        dt_utc = parse_api_datetime(str(row.get("Date") or ""), assume_utc=True)
        return CalendarEvent(
            event_id=str(row.get("CalendarID") or row.get("CalendarId") or title_en + dt_utc.isoformat()),
            title=self.translator.translate(title_en),
            title_en=title_en,
            currency=ccy,
            country=country,
            importance=_imp_te(row.get("Importance")),
            dt_utc=dt_utc,
            dt_tehran=to_tehran(dt_utc),
            forecast=str(row.get("Forecast") or "-"),
            previous=str(row.get("Previous") or "-"),
            actual=str(row.get("Actual") or "-"),
        )

    def _finnhub(self, target: date) -> list[CalendarEvent]:
        key = self.settings.finnhub_key
        if not key:
            raise CalendarFetchError("FINNHUB_API_KEY missing")
        url = "https://finnhub.io/api/v1/calendar/economic"
        resp = _retry_get(url, {"from": target.isoformat(), "to": target.isoformat(), "token": key})
        payload = resp.json()
        rows = payload.get("economicCalendar") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            raise CalendarFetchError("invalid Finnhub payload")
        events: list[CalendarEvent] = []
        for row in rows:
            try:
                events.append(self._from_fh(row))
            except Exception:
                continue
        return events

    def _from_fh(self, row: dict) -> CalendarEvent:
        title_en = str(row.get("event") or "").strip()
        country = str(row.get("country") or "").strip()
        ccy = COUNTRY_CCY.get(country.lower(), country.upper()[:3] if len(country) == 2 else "")
        # ISO country codes common in Finnhub
        iso = {
            "US": "USD", "EU": "EUR", "GB": "GBP", "UK": "GBP", "JP": "JPY",
            "CA": "CAD", "AU": "AUD", "NZ": "NZD", "CH": "CHF", "CN": "CNY", "DE": "EUR",
        }
        ccy = iso.get(country.upper(), ccy)
        dt_utc = parse_api_datetime(str(row.get("time") or ""), assume_utc=True)
        return CalendarEvent(
            event_id=f"{title_en}-{dt_utc.isoformat()}",
            title=self.translator.translate(title_en),
            title_en=title_en,
            currency=ccy,
            country=country,
            importance=_imp_fh(row.get("impact")),
            dt_utc=dt_utc,
            dt_tehran=to_tehran(dt_utc),
            forecast=str(row.get("estimate") if row.get("estimate") is not None else "-"),
            previous=str(row.get("prev") if row.get("prev") is not None else "-"),
            actual=str(row.get("actual") if row.get("actual") is not None else "-"),
            unit=str(row.get("unit") or ""),
        )

    def _mock(self, target: date) -> list[CalendarEvent]:
        path = self.fixtures_dir / "sample_calendar.json"
        with open(path, encoding="utf-8") as fh:
            rows = json.load(fh)
        events: list[CalendarEvent] = []
        base = datetime(target.year, target.month, target.day, tzinfo=timezone.utc)
        for row in rows:
            hour, minute = [int(x) for x in row["time_utc"].split(":")]
            dt_utc = base.replace(hour=hour, minute=minute)
            title_en = row["event"]
            events.append(
                CalendarEvent(
                    event_id=row.get("id", title_en),
                    title=self.translator.translate(title_en),
                    title_en=title_en,
                    currency=row["currency"],
                    country=row.get("country", ""),
                    importance=int(row["importance"]),
                    dt_utc=dt_utc,
                    dt_tehran=to_tehran(dt_utc),
                    forecast=str(row.get("forecast", "-")),
                    previous=str(row.get("previous", "-")),
                    actual=str(row.get("actual", "-")),
                )
            )
        return events
