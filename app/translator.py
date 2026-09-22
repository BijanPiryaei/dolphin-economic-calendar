from __future__ import annotations

import json
from pathlib import Path


class Translator:
    def __init__(self, path: Path) -> None:
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
        self.events = {k.lower(): v for k, v in payload.get("events", {}).items()}
        self.contains = payload.get("contains", {})

    def translate(self, title: str) -> str:
        key = (title or "").strip()
        if not key:
            return "-"
        hit = self.events.get(key.lower())
        if hit:
            return hit
        lower = key.lower()
        for needle, fa in self.contains.items():
            if needle.lower() in lower:
                return f"{fa} ({key})"
        return key
