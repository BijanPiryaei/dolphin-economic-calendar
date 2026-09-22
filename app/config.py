from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


def _load_env() -> None:
    load_dotenv(ROOT / ".env")


def _split_csv(value: str) -> list[str]:
    return [p.strip() for p in value.split(",") if p.strip()]


def _split_ids(value: str) -> list[int]:
    out: list[int] = []
    for part in _split_csv(value):
        try:
            out.append(int(part))
        except ValueError:
            continue
    return out


@dataclass(frozen=True)
class Settings:
    api_provider: str
    trading_economics_key: str
    finnhub_key: str
    telegram_bot_token: str
    telegram_channel_id: str
    admin_user_ids: list[int]
    enable_admin_alerts: bool
    enable_admin_bot: bool
    post_time: str
    timezone: str
    min_importance: int
    enabled_currencies: list[str]
    max_events_per_image: int
    enable_update_mode: bool
    log_level: str
    brand_name: str
    website: str
    colors: dict
    layout: dict
    importance_map: dict
    root: Path


def load_settings() -> Settings:
    _load_env()
    with open(ROOT / "config.yaml", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    brand = raw.get("brand", {})
    return Settings(
        api_provider=os.getenv("API_PROVIDER", "mock").strip().lower(),
        trading_economics_key=os.getenv("TRADING_ECONOMICS_API_KEY", "").strip(),
        finnhub_key=os.getenv("FINNHUB_API_KEY", "").strip(),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        telegram_channel_id=os.getenv("TELEGRAM_CHANNEL_ID", "").strip(),
        admin_user_ids=_split_ids(os.getenv("ADMIN_USER_IDS", "")),
        enable_admin_alerts=os.getenv("ENABLE_ADMIN_ALERTS", "true").lower() == "true",
        enable_admin_bot=os.getenv("ENABLE_ADMIN_BOT", "true").lower() == "true",
        post_time=os.getenv("POST_TIME", "22:00").strip(),
        timezone=os.getenv("TIMEZONE", "Asia/Tehran").strip(),
        min_importance=int(os.getenv("MIN_IMPORTANCE", "2")),
        enabled_currencies=[c.upper() for c in _split_csv(os.getenv(
            "ENABLED_CURRENCIES", "USD,EUR,GBP,JPY,CAD,AUD,NZD,CHF"
        ))],
        max_events_per_image=int(os.getenv("MAX_EVENTS_PER_IMAGE", "14")),
        enable_update_mode=os.getenv("ENABLE_UPDATE_MODE", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        brand_name=brand.get("name", "Dolfin Traders"),
        website=brand.get("website", "https://dolphintraders.ir"),
        colors=raw.get("colors", {}),
        layout=raw.get("layout", {}),
        importance_map=raw.get("importance_map", {}),
        root=ROOT,
    )
