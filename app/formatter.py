from __future__ import annotations

import jdatetime

WEEKDAYS = {
    0: "دوشنبه",
    1: "سه‌شنبه",
    2: "چهارشنبه",
    3: "پنجشنبه",
    4: "جمعه",
    5: "شنبه",
    6: "یکشنبه",
}

MONTHS = {
    1: "فروردین",
    2: "اردیبهشت",
    3: "خرداد",
    4: "تیر",
    5: "مرداد",
    6: "شهریور",
    7: "مهر",
    8: "آبان",
    9: "آذر",
    10: "دی",
    11: "بهمن",
    12: "اسفند",
}


def jalali_long(d) -> str:
    j = jdatetime.date.fromgregorian(date=d)
    weekday = WEEKDAYS[d.weekday()]
    month = MONTHS[j.month]
    return f"{weekday} {j.day} {month} {j.year}"


def display_value(value: str | None) -> str:
    text = str(value).strip() if value is not None else ""
    if text in {"", "None", "null", "nan"}:
        return "-"
    return text