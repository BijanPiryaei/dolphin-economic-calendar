from __future__ import annotations

import json
import time
from pathlib import Path

import requests

from app.prices import fetch_quotes, format_message


class PricePublisher:
    def __init__(self, token: str, channel_id: str, state_path: Path) -> None:
        self.token = token
        self.channel_id = channel_id
        self.state_path = state_path
        self.base = f"https://api.telegram.org/bot{token}"

    def _state(self) -> dict:
        if self.state_path.exists():
            try:
                return json.loads(self.state_path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save(self, data: dict) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(data), encoding="utf-8")

    def publish(self) -> str:
        if not self.token or not self.channel_id:
            raise RuntimeError("TELEGRAM_BOT_TOKEN or TELEGRAM_PRICE_CHANNEL_ID missing")
        text = format_message(fetch_quotes())
        state = self._state()
        msg_id = state.get("message_id")
        if msg_id:
            resp = requests.post(
                f"{self.base}/editMessageText",
                json={
                    "chat_id": self.channel_id,
                    "message_id": int(msg_id),
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                timeout=30,
            )
            data = resp.json()
            if data.get("ok"):
                return "edited"
        resp = requests.post(
            f"{self.base}/sendMessage",
            json={
                "chat_id": self.channel_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=30,
        )
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(str(data))
        self._save({"message_id": data["result"]["message_id"]})
        return "sent"

    def loop(self, seconds: int = 10) -> None:
        while True:
            try:
                action = self.publish()
                print(action, flush=True)
            except Exception as exc:
                print("error", exc, flush=True)
            time.sleep(max(int(seconds), 3))
