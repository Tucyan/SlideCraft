from dataclasses import dataclass, field
from typing import Dict


@dataclass
class CompileContext:
    canvas_w: int
    canvas_h: int
    slide_w_emu: int
    slide_h_emu: int
    language: str
    theme: Dict
    assets: Dict[str, Dict]
    asset_manager: object = field(repr=False)
