import io
import base64
import urllib.request
from pathlib import Path
from typing import Dict, Tuple

from PIL import Image


def image_size_from_bytes(data: bytes) -> Tuple[int, int]:
    with Image.open(io.BytesIO(data)) as img:
        return img.size


def crop_to_fill(img_w: int, img_h: int, box_w: int, box_h: int) -> Tuple[float, float, float, float]:
    img_ratio = img_w / img_h
    box_ratio = box_w / box_h

    if img_ratio > box_ratio:
        src_h = img_h
        src_w = int(src_h * box_ratio)
        src_x = (img_w - src_w) / 2
        src_y = 0
    else:
        src_w = img_w
        src_h = int(src_w / box_ratio)
        src_x = 0
        src_y = (img_h - src_h) / 2

    return src_x, src_y, src_w, src_h


def pil_load_from_bytes(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data)).convert("RGBA")


def pil_to_png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def fit_image_bytes_to_mode(data: bytes, mode: str, box_w: int, box_h: int) -> bytes:
    img = pil_load_from_bytes(data)

    if mode == "stretch":
        out = img.resize((box_w, box_h))
        return pil_to_png_bytes(out)

    if mode == "contain":
        scale = min(box_w / img.width, box_h / img.height)
        new_w = max(1, int(img.width * scale))
        new_h = max(1, int(img.height * scale))
        resized = img.resize((new_w, new_h))
        canvas = Image.new("RGBA", (box_w, box_h), (255, 255, 255, 0))
        paste_x = (box_w - new_w) // 2
        paste_y = (box_h - new_h) // 2
        canvas.paste(resized, (paste_x, paste_y), resized)
        return pil_to_png_bytes(canvas)

    # cover
    src_x, src_y, src_w, src_h = crop_to_fill(img.width, img.height, box_w, box_h)
    cropped = img.crop((int(src_x), int(src_y), int(src_x + src_w), int(src_y + src_h)))
    out = cropped.resize((box_w, box_h))
    return pil_to_png_bytes(out)


def source_to_bytes(source: Dict) -> bytes:
    stype = source.get("type")
    value = source.get("value")

    if stype == "local":
        return Path(value).read_bytes()

    if stype == "url":
        max_retries = 3
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(value, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return resp.read()
            except Exception as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(1)
                    continue
                raise e

    if stype == "base64":
        if "," in value and value.startswith("data:"):
            value = value.split(",", 1)[1]
        return base64.b64decode(value)

    raise ValueError(f"Unsupported asset source type: {stype}")
