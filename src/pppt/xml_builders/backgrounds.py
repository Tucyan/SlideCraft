from typing import Dict

from ..context import CompileContext
from ..utils import hex_to_rgb
from .common import build_gradient_fill_xml


def build_slide_bg_xml(ctx: CompileContext, slide: Dict) -> str:
    bg = slide.get("background") or ctx.theme.get("background_default")
    if not bg:
        return ""

    bg_type = bg.get("type")

    if bg_type == "color":
        color = hex_to_rgb(bg.get("color", "#FFFFFF"), "FFFFFF")
        return f'''
            <p:bg>
              <p:bgPr>
                <a:solidFill><a:srgbClr val="{color}"/></a:solidFill>
                <a:effectLst/>
              </p:bgPr>
            </p:bg>
            '''

    if bg_type == "gradient":
        gradient = bg.get("gradient", {})
        gradient_xml = build_gradient_fill_xml(gradient)
        return f'''
            <p:bg>
              <p:bgPr>
                {gradient_xml}
                <a:effectLst/>
              </p:bgPr>
            </p:bg>
            '''

    return ""
