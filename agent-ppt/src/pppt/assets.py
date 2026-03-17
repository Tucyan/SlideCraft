import io
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image

try:
    import cairosvg
except ImportError:
    cairosvg = None

from .constants import CONTENT_TYPE_PNG, CONTENT_TYPE_JPEG
from .image_utils import (
    source_to_bytes, fit_image_bytes_to_mode,
    pil_load_from_bytes, pil_to_png_bytes,
)


class AssetManager:
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.asset_bytes_cache: Dict[str, bytes] = {}
        self.media_counter = 1
        self.media_entries: List[Tuple[str, bytes, str]] = []
        self.asset_media_map: Dict[str, Tuple[str, str]] = {}
        self.chart_counter: int = 1
        self.chart_entries: List[Tuple[str, str]] = []  # (chart_path, chart_xml)

    def add_chart(self, chart_xml: str) -> Tuple[str, str]:
        """
        Register a chart XML string and return (chart_path, rel_target).
        chart_path  = "ppt/charts/chartN.xml"
        rel_target  = "../charts/chartN.xml"
        """
        chart_name = f"chart{self.chart_counter}.xml"
        chart_path = f"ppt/charts/{chart_name}"
        rel_target = f"../charts/{chart_name}"
        self.chart_counter += 1
        self.chart_entries.append((chart_path, chart_xml))
        return chart_path, rel_target

    def load_asset_bytes(self, asset: Dict) -> bytes:
        asset_id = asset["asset_id"]
        if asset_id in self.asset_bytes_cache:
            return self.asset_bytes_cache[asset_id]
        data = source_to_bytes(asset["source"])
        self.asset_bytes_cache[asset_id] = data
        return data

    def add_media(self, data: bytes, ext: str) -> Tuple[str, str]:
        media_name = f"image{self.media_counter}.{ext}"
        media_path = f"ppt/media/{media_name}"
        self.media_counter += 1

        if ext.lower() == "png":
            ctype = CONTENT_TYPE_PNG
        else:
            ctype = CONTENT_TYPE_JPEG

        self.media_entries.append((media_path, data, ctype))
        return media_name, ctype

    def materialize_asset_image(
        self,
        asset: Dict,
        fit_mode: Optional[str] = None,
        target_w_px: Optional[int] = None,
        target_h_px: Optional[int] = None
    ) -> Tuple[str, str]:
        asset_id = asset["asset_id"]
        kind = asset.get("kind", "")
        mime_type = (asset.get("mime_type") or "").lower()

        cache_key = f"{asset_id}|{fit_mode}|{target_w_px}|{target_h_px}"
        if cache_key in self.asset_media_map:
            return self.asset_media_map[cache_key]

        try:
            raw = self.load_asset_bytes(asset)
        except Exception as e:
            print(f"Warning: Failed to load asset {asset_id}: {e}, creating placeholder")
            target_w = target_w_px or 400
            target_h = target_h_px or 300
            img = Image.new('RGB', (target_w, target_h), color='#E0E0E0')
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            draw.text((target_w//4, target_h//2), f"Image: {asset_id}", fill=(100, 100, 100))
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            png_bytes = buf.getvalue()
            media_name, ctype = self.add_media(png_bytes, "png")
            self.asset_media_map[cache_key] = (media_name, ctype)
            return media_name, ctype

        if kind == "svg" or mime_type == "image/svg+xml":
            if cairosvg is not None:
                png_bytes = cairosvg.svg2png(bytestring=raw)
            else:
                print(f"Warning: cairosvg not available, creating placeholder for SVG asset {asset_id}")
                target_w = target_w_px or 400
                target_h = target_h_px or 300
                img = Image.new('RGB', (target_w, target_h), color='#F0F0F0')
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                png_bytes = buf.getvalue()
            if fit_mode and target_w_px and target_h_px:
                png_bytes = fit_image_bytes_to_mode(png_bytes, fit_mode, target_w_px, target_h_px)
            media_name, ctype = self.add_media(png_bytes, "png")
            self.asset_media_map[cache_key] = (media_name, ctype)
            return media_name, ctype

        # Normal image
        if "png" in mime_type:
            ext = "png"
        elif "jpeg" in mime_type or "jpg" in mime_type:
            ext = "jpg"
        else:
            raw = pil_to_png_bytes(pil_load_from_bytes(raw))
            ext = "png"

        if fit_mode and target_w_px and target_h_px:
            out_bytes = fit_image_bytes_to_mode(raw, fit_mode, target_w_px, target_h_px)
            media_name, ctype = self.add_media(out_bytes, "png")
            self.asset_media_map[cache_key] = (media_name, ctype)
            return media_name, ctype

        media_name, ctype = self.add_media(raw, ext)
        self.asset_media_map[cache_key] = (media_name, ctype)
        return media_name, ctype
