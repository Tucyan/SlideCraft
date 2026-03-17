import re
from pathlib import Path
from typing import Dict, Tuple
from xml.sax.saxutils import escape

from .constants import EMU_PER_INCH


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, content: str):
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")


def write_bytes(path: Path, data: bytes):
    ensure_dir(path.parent)
    path.write_bytes(data)


def sanitize_xml_text(s: str) -> str:
    return escape(s or "")


def hex_to_rgb(hex_color: str, default: str = "000000") -> str:
    if not hex_color:
        return default
    s = hex_color.strip().replace("#", "")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) != 6 or not re.fullmatch(r"[0-9a-fA-F]{6}", s):
        return default
    return s.upper()


def canvas_to_slide_emu(canvas_w: int, canvas_h: int) -> Tuple[int, int]:
    known = {
        (1920, 1080): (12192000, 6858000),  # 16:9
        (1440, 1080): (9144000, 6858000),   # 4:3
    }
    if (canvas_w, canvas_h) in known:
        return known[(canvas_w, canvas_h)]
    dpi = 96
    return (int(canvas_w / dpi * EMU_PER_INCH), int(canvas_h / dpi * EMU_PER_INCH))


def px_to_emu_x(x: float, canvas_w: int, slide_w_emu: int) -> int:
    return int(x / canvas_w * slide_w_emu)


def px_to_emu_y(y: float, canvas_h: int, slide_h_emu: int) -> int:
    return int(y / canvas_h * slide_h_emu)


def rect_px_to_emu(rect: Dict, canvas_w: int, canvas_h: int, slide_w_emu: int, slide_h_emu: int) -> Tuple[int, int, int, int]:
    x = int(rect.get("x", 0))
    y = int(rect.get("y", 0))
    w = int(rect.get("w", 0))
    h = int(rect.get("h", 0))
    return (
        px_to_emu_x(x, canvas_w, slide_w_emu),
        px_to_emu_y(y, canvas_h, slide_h_emu),
        px_to_emu_x(w, canvas_w, slide_w_emu),
        px_to_emu_y(h, canvas_h, slide_h_emu),
    )


def shape_type_to_ppt_prst(shape_type: str) -> str:
    mapping = {
        "rect": "rect",
        "round_rect": "roundRect",
        "ellipse": "ellipse",
        "line": "line",
        "triangle": "triangle",
        "diamond": "diamond",
        "arrow": "rightArrow",
        "chevron": "chevron",
        "callout": "wedgeRoundRectCallout",
    }
    return mapping.get(shape_type, "rect")


def paragraphs_from_text_element(text_block: Dict):
    paragraphs = text_block.get("paragraphs", [])
    if not paragraphs:
        return [{"runs": [{"text": ""}]}]
    return paragraphs
