from __future__ import annotations

from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.formatter import jalali_long
from app.models import CalendarEvent
from app.text_rtl import rtl
from app.timezone_utils import format_tehran_clock

IMPACT = {
    3: ("بسیارمهم", "#E11D48"),
    2: ("مهم", "#F59E0B"),
    1: ("معمولی", "#2563EB"),
}


def _font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def _hex(colors: dict, key: str, default: str) -> str:
    return colors.get(key, default)


def render_calendar(events, target, settings, out_dir, page_size=None):
    out_dir.mkdir(parents=True, exist_ok=True)
    fonts = settings.root / "assets" / "fonts"
    regular = fonts / "Vazirmatn-Regular.ttf"
    bold = fonts / "Vazirmatn-Bold.ttf"
    logo = settings.root / "assets" / "logo.png"
    page_size = page_size or settings.max_events_per_image
    chunks = [events[i : i + page_size] for i in range(0, max(len(events), 1), page_size)] or [[]]
    paths = []
    total = len(chunks)
    for idx, chunk in enumerate(chunks, start=1):
        path = out_dir / f"calendar-{target.isoformat()}-p{idx}.png"
        _draw_page(chunk, target, settings, regular, bold, logo, path, idx, total)
        paths.append(path)
    return paths


def _draw_page(events, target, settings, regular, bold, logo, path, page, total):
    colors = settings.colors
    width = int(settings.layout.get("width", 1080))
    row_h = int(settings.layout.get("row_height", 56))
    header_h = int(settings.layout.get("header_height", 150))
    footer_h = int(settings.layout.get("footer_height", 70))
    margin = int(settings.layout.get("margin", 28))
    rows = max(len(events), 1)
    height = header_h + 90 + rows * row_h + footer_h + 40
    img = Image.new("RGB", (width, height), _hex(colors, "background_bottom", "#4A1D7A"))
    draw = ImageDraw.Draw(img)
    _gradient(draw, width, height, colors)

    pill = [width // 2 - 210, 28, width // 2 + 210, 88]
    draw.rounded_rectangle(pill, radius=24, fill=_hex(colors, "header_pill", "#3B1468"))
    title = rtl(settings.brand_name, persian_digits=False)
    f_brand = _font(bold, 30)
    tw = draw.textlength(title, font=f_brand)
    draw.text(((width - tw) / 2, 42), title, font=f_brand, fill="white")

    f_small = _font(regular, 18)
    f_year = _font(bold, 28)
    draw.text((width - margin - 8, 28), rtl("تقویم اقتصادی"), font=f_small, fill="white", anchor="ra")
    draw.text((width - margin - 8, 54), rtl(str(target.year)), font=f_year, fill="white", anchor="ra")

    if logo.exists():
        mark = Image.open(logo).convert("RGBA")
        mark.thumbnail((86, 86))
        img.paste(mark, (margin, 22), mark)
    else:
        draw.rounded_rectangle([margin, 22, margin + 86, 108], radius=18, fill="#C4B5FD")
        draw.text((margin + 43, 52), "DT", font=_font(bold, 20), fill="#3B1468", anchor="mm")

    card = [margin, header_h - 20, width - margin, height - footer_h]
    draw.rounded_rectangle(card, radius=26, fill="white")

    jlabel = jalali_long(target)
    f_day = _font(bold, 22)
    draw.text((width - margin - 36, header_h + 8), rtl(jlabel), font=f_day, fill=_hex(colors, "date_block", "#3B1468"), anchor="ra")
    draw.text((width - margin - 36, header_h + 36), target.strftime("%Y/%m/%d"), font=f_small, fill="#8B83A0", anchor="ra")
    if total > 1:
        draw.text((margin + 36, header_h + 20), rtl(f"صفحه {page} از {total}"), font=f_small, fill="#8B83A0")

    headers = [("قبلی", 80), ("پیش‌بینی", 175), ("واقعی", 270), ("تأثیر", 365), ("رویداد", 640), ("ارز", 900), ("زمان", 1015)]
    y0 = header_h + 78
    for label, x in headers:
        draw.text((x, y0), rtl(label), font=_font(bold, 15), fill="#6B6280", anchor="mm")
    draw.line([(margin + 16, y0 + 18), (width - margin - 16, y0 + 18)], fill="#E6E0F0", width=1)

    f_row = _font(regular, 16)
    f_ev = _font(regular, 14)
    f_badge = _font(bold, 13)
    flags_dir = settings.root / "assets" / "flags"
    y = y0 + 22
    event_right = 820
    event_max_w = 430
    if not events:
        draw.text((width / 2, y + 20), rtl("رویداد فیلترشده‌ای برای این روز نیست"), font=f_row, fill="#6B6280", anchor="mm")
    for i, ev in enumerate(events):
        if i % 2 == 1:
            draw.rectangle([margin + 12, y, width - margin - 12, y + row_h], fill="#F6F3FA")
        mid = y + row_h / 2
        clock = format_tehran_clock(ev.dt_tehran)
        draw.text((1015, mid), rtl(clock), font=f_row, fill="#2B2140", anchor="mm")
        _paste_flag(img, flags_dir, ev.currency, 868, int(y + (row_h - 18) / 2))
        draw.text((912, mid), ev.currency, font=_font(bold, 15), fill="#2B2140", anchor="lm")
        title = _fit_text(draw, rtl(ev.title), f_ev, event_max_w)
        draw.text((event_right, mid), title, font=f_ev, fill="#2B2140", anchor="rm")
        badge, color = IMPACT.get(ev.importance, IMPACT[1])
        bw = 72
        bx = 365
        draw.rounded_rectangle([bx - bw / 2, y + 14, bx + bw / 2, y + row_h - 14], radius=12, fill=color)
        draw.text((bx, mid), rtl(badge), font=f_badge, fill="white", anchor="mm")
        draw.text((270, mid), rtl(_dash(ev.actual)), font=f_row, fill="#2B2140", anchor="mm")
        draw.text((175, mid), rtl(_dash(ev.forecast)), font=f_row, fill="#2B2140", anchor="mm")
        draw.text((80, mid), rtl(_dash(ev.previous)), font=f_row, fill="#2B2140", anchor="mm")
        y += row_h

    fy = height - 42
    draw.text((margin + 8, fy), "dolphintraders.ir", font=_font(bold, 16), fill="white")
    draw.text((width - margin - 8, fy), rtl("همه زمان‌ها بر اساس زمان تهران هستند"), font=f_small, fill="white", anchor="ra")
    _save_png(img, path)


def _save_png(img, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.stem + "-tmp.png")
    img.save(tmp, "PNG", optimize=True)
    try:
        tmp.replace(path)
    except OSError:
        fallback = path.with_name(path.stem + "-new.png")
        tmp.replace(fallback)


def _fit_text(draw, text: str, font, max_w: float) -> str:
    if draw.textlength(text, font=font) <= max_w:
        return text
    ell = "…"
    out = text
    while out and draw.textlength(out + ell, font=font) > max_w:
        out = out[:-1]
    return (out + ell) if out else ell


def _paste_flag(img, flags_dir: Path, currency: str, x: int, y: int) -> None:
    code = (currency or "").upper()
    path = flags_dir / f"{code}.png"
    if not path.exists() and code == "EUR":
        path = flags_dir / "EU.png"
    if not path.exists():
        return
    try:
        flag = Image.open(path).convert("RGBA")
        flag.thumbnail((28, 18))
        img.paste(flag, (x, y), flag)
    except Exception:
        return


def _dash(value):
    text = (value or "").strip()
    return "-" if text in {"", "-", "None", "null"} else text


def _gradient(draw, w, h, colors):
    top = colors.get("background_top", "#6B2FA0").lstrip("#")
    bot = colors.get("background_bottom", "#4A1D7A").lstrip("#")
    tr, tg, tb = int(top[0:2], 16), int(top[2:4], 16), int(top[4:6], 16)
    br, bg, bb = int(bot[0:2], 16), int(bot[2:4], 16), int(bot[4:6], 16)
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(tr + (br - tr) * t)
        g = int(tg + (bg - tg) * t)
        b = int(tb + (bb - tb) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
