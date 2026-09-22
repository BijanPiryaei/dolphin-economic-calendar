from __future__ import annotations

from pathlib import Path

import requests


class TelegramError(Exception):
    pass


class TelegramClient:
    def __init__(self, token: str, channel_id: str) -> None:
        self.token = token
        self.channel_id = channel_id
        self.base = f"https://api.telegram.org/bot{token}"

    def send_photo(self, image: Path, caption: str) -> str:
        if not self.token or not self.channel_id:
            raise TelegramError("Telegram token or channel is missing")
        with open(image, "rb") as fh:
            resp = requests.post(
                f"{self.base}/sendPhoto",
                data={"chat_id": self.channel_id, "caption": caption},
                files={"photo": fh},
                timeout=60,
            )
        data = resp.json() if resp.content else {}
        if not data.get("ok"):
            raise TelegramError(str(data))
        return str(data["result"]["message_id"])

    def send_media_group(self, images: list[Path], caption: str) -> str:
        if len(images) == 1:
            return self.send_photo(images[0], caption)
        media = []
        files = {}
        for i, path in enumerate(images):
            key = f"photo{i}"
            item = {"type": "photo", "media": f"attach://{key}"}
            if i == 0:
                item["caption"] = caption
            media.append(item)
            files[key] = open(path, "rb")
        try:
            resp = requests.post(
                f"{self.base}/sendMediaGroup",
                data={"chat_id": self.channel_id, "media": __import__("json").dumps(media)},
                files=files,
                timeout=90,
            )
        finally:
            for fh in files.values():
                fh.close()
        data = resp.json() if resp.content else {}
        if not data.get("ok"):
            raise TelegramError(str(data))
        first = data["result"][0]
        return str(first.get("message_id", ""))

    def send_message(self, chat_id: str | int, text: str) -> None:
        if not self.token:
            raise TelegramError("Telegram token missing")
        resp = requests.post(
            f"{self.base}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=30,
        )
        data = resp.json() if resp.content else {}
        if not data.get("ok"):
            raise TelegramError(str(data))
