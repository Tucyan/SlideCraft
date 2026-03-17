import json
import shutil
from pathlib import Path
from typing import Dict, Tuple

from .constants import DEFAULT_CANVAS_W, DEFAULT_CANVAS_H
from .context import CompileContext
from .utils import ensure_dir, write_text, write_bytes, canvas_to_slide_emu
from .assets import AssetManager
from .ooxml.package import write_root_rels, write_content_types, zip_to_pptx
from .ooxml.presentation import write_doc_props, write_theme, write_slide_master, write_slide_layout, write_presentation
from .ooxml.slides import build_single_slide_xml


class JsonToPptxExporter:
    def __init__(self, doc: Dict, output_path: str):
        self.doc = doc
        self.output_path = Path(output_path).resolve()
        self.work_dir = self.output_path.parent / f".pptx_build_{self.output_path.stem}"
        self.asset_manager = AssetManager(self.work_dir)

        self.slides = self.doc.get("slides", [])
        self.assets = {a["asset_id"]: a for a in self.doc.get("assets", [])}
        self.theme = self.doc.get("theme", {})
        self.metadata = self.doc.get("metadata", {})

        self.canvas_w, self.canvas_h = self._resolve_canvas_size()
        self.slide_w_emu, self.slide_h_emu = canvas_to_slide_emu(self.canvas_w, self.canvas_h)
        self.language = self.metadata.get("language", "zh-CN")

    def _resolve_canvas_size(self) -> Tuple[int, int]:
        theme = self.doc.get("theme", {})
        slide_size = theme.get("slide_size", "16:9")
        if slide_size == "4:3":
            return 1440, 1080
        if slide_size == "custom":
            return int(theme.get("width_px", DEFAULT_CANVAS_W)), int(theme.get("height_px", DEFAULT_CANVAS_H))
        return DEFAULT_CANVAS_W, DEFAULT_CANVAS_H

    def _make_context(self) -> CompileContext:
        return CompileContext(
            canvas_w=self.canvas_w,
            canvas_h=self.canvas_h,
            slide_w_emu=self.slide_w_emu,
            slide_h_emu=self.slide_h_emu,
            language=self.language,
            theme=self.theme,
            assets=self.assets,
            asset_manager=self.asset_manager,
        )

    def build(self):
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)
        ensure_dir(self.work_dir)

        self._build_dirs()
        ctx = self._make_context()

        write_root_rels(self.work_dir)
        write_doc_props(self.work_dir, self.metadata, len(self.slides))
        write_theme(self.work_dir, self.theme)
        write_slide_master(self.work_dir)
        write_slide_layout(self.work_dir)
        write_presentation(self.work_dir, ctx, len(self.slides))
        self._write_slides(ctx)
        self._write_media()
        self._write_charts()
        write_content_types(
            self.work_dir,
            len(self.slides),
            chart_count=self.asset_manager.chart_counter - 1,
        )
        zip_to_pptx(self.work_dir, self.output_path)

    def _build_dirs(self):
        dirs = [
            "_rels",
            "docProps",
            "ppt",
            "ppt/_rels",
            "ppt/theme",
            "ppt/slideMasters",
            "ppt/slideMasters/_rels",
            "ppt/slideLayouts",
            "ppt/slideLayouts/_rels",
            "ppt/slides",
            "ppt/slides/_rels",
            "ppt/media",
            "ppt/charts",
        ]
        for d in dirs:
            ensure_dir(self.work_dir / d)

    def _write_slides(self, ctx: CompileContext):
        for idx, slide in enumerate(self.slides, start=1):
            slide_xml, slide_rels = build_single_slide_xml(ctx, slide, idx)
            write_text(self.work_dir / f"ppt/slides/slide{idx}.xml", slide_xml)
            write_text(self.work_dir / f"ppt/slides/_rels/slide{idx}.xml.rels", slide_rels)

    def _write_media(self):
        for media_path, data, _ctype in self.asset_manager.media_entries:
            write_bytes(self.work_dir / media_path, data)

    def _write_charts(self):
        for chart_path, chart_xml in self.asset_manager.chart_entries:
            write_text(self.work_dir / chart_path, chart_xml)

    @staticmethod
    def from_json_file(json_path: str, output_path: str):
        doc = json.loads(Path(json_path).read_text(encoding="utf-8"))
        exporter = JsonToPptxExporter(doc, output_path)
        exporter.build()
