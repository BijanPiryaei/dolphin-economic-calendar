from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

TEHRAN = ZoneInfo("Asia/Tehran")
POSTS = 10


class GoldError(Exception):
    pass


def fetch_gold() -> float | None:
    headers = {"User-Agent": "Mozilla/5.0 DolphinTraders/1.0"}
    for ticker in ("XAUUSD=X", "GC=F"):
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            r = requests.get(url, params={"range": "1d", "interval": "1m"}, headers=headers, timeout=12)
            r.raise_for_status()
            meta = r.json()["chart"]["result"][0]["meta"]
            price = meta.get("regularMarketPrice") or meta.get("previousClose")
            if price:
                return float(price)
        except Exception:
            continue
    return None


def format_gold(price: float | None, slot: int) -> str:
    now = datetime.now(TEHRAN).strftime("%H:%M:%S")
    val = f"{price:,.2f}" if price is not None else "—"
    return (
        "🥇 <b>انس طلای جهانی</b>\n"
        "XAU / USD\n"
        "────────────\n"
        f"<b>{val}</b> دلار\n"
        "────────────\n"
        f"🕐 تهران {now}\n"
        f"پست {slot + 1} از {POSTS}\n"
        "منبع: Yahoo Finance\n"
        "تأخیر دارد · توصیه مالی نیست\n"
        "🌐 https://dolphintraders.ir"
    )


class GoldPublisher:
    def __init__(self, token: str, channel: str, store: Path) -> None:
        self.token = token
        self.channel = channel
        self.store = store
        self.base = f"https://api.telegram.org/bot{token}"

    def _api(self, method: str, payload: dict) -> dict:
        if not self.token or not self.channel:
            raise GoldError("token or gold channel missing")
        r = requests.post(f"{self.base}/{method}", json=payload, timeout=30)
        data = r.json() if r.content else {}
        if not data.get("ok"):
            raise GoldError(str(data))
        return data

    def _load(self) -> list[int]:
        if not self.store.exists():
            return []
        raw = json.loads(self.store.read_text(encoding="utf-8"))
        return [int(x) for x in raw.get("message_ids", [])]

    def _save(self, ids: list[int], index: int = 0) -> None:
        self.store.parent.mkdir(parents=True, exist_ok=True)
        self.store.write_text(
            json.dumps({"message_ids": ids, "index": index}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def init_posts(self) -> list[int]:
        price = fetch_gold()
        ids = []
        for i in range(POSTS):
            data = self._api(
                "sendMessage",
                {
                    "chat_id": self.channel,
                    "text": format_gold(price, i),
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
            )
            ids.append(int(data["result"]["message_id"]))
            time.sleep(1.2)
        self._save(ids, 0)
        return ids

    def edit_next(self) -> str:
        ids = self._load()
        if len(ids) != POSTS:
            ids = self.init_posts()
        state = json.loads(self.store.read_text(encoding="utf-8"))
        index = int(state.get("index", 0)) % POSTS
        price = fetch_gold()
        try:
            self._api(
                "editMessageText",
                {
                    "chat_id": self.channel,
                    "message_id": ids[index],
                    "text": format_gold(price, index),
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
            )
        except GoldError as exc:
            if "message is not modified" in str(exc):
                pass
            else:
                raise
        nxt = (index + 1) % POSTS
        self._save(ids, nxt)
        val = f"{price:,.2f}" if price is not None else "—"
        return f"edited slot {index + 1}/{POSTS} price={val}"

    def loop(self, interval: int = 3) -> None:
        wait = max(3, int(interval))
        while True:
            try:
                print(self.edit_next(), flush=True)
            except Exception as exc:
                print(f"gold loop error: {exc}", flush=True)
                time.sleep(max(wait, 15))
                continue
            time.sleep(wait)
