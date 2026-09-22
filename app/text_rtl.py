from __future__ import annotations

import os
import sys

import arabic_reshaper
from bidi.algorithm import get_display

PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def rtl(text: str, persian_digits: bool = True) -> str:
    raw = str(text or "")
    if persian_digits:
        raw = raw.translate(PERSIAN_DIGITS)
    mode = os.getenv("RTL_MODE", "").strip().lower()
    if not mode:
        mode = "bidi" if sys.platform == "win32" else "raw"
    if mode == "raw":
        return raw
    shaped = arabic_reshaper.reshape(raw)
    if mode == "reshape":
        return shaped
    return get_display(shaped)
