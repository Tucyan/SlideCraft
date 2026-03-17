from typing import Dict

from ..context import CompileContext
from ..utils import sanitize_xml_text, rect_px_to_emu, shape_type_to_ppt_prst, paragraphs_from_text_element
from .common import build_solid_fill_xml, build_line_xml
from .text import build_paragraphs_xml


def _build_xfrm_xml(x: int, y: int, cx: int, cy: int, rotation: float = 0) -> str:
    rot_attr = f' rot="{int(rotation * 60000)}"' if rotation else ""
    return f'''<a:xfrm{rot_attr}>
              <a:off x="{x}" y="{y}"/>
              <a:ext cx="{cx}" cy="{cy}"/>
            </a:xfrm>'''


def build_textbox_xml(ctx: CompileContext, elem: Dict, shape_id: int) -> str:
    x, y, cx, cy = rect_px_to_emu(elem["bbox"], ctx.canvas_w, ctx.canvas_h, ctx.slide_w_emu, ctx.slide_h_emu)
    name = sanitize_xml_text(elem.get("name", elem.get("id", f"TextBox {shape_id}")))
    paragraphs = paragraphs_from_text_element(elem.get("text", {}))
    rotation = elem.get("rotation", 0)
    opacity = elem.get("opacity", 1.0)

    tx_style = elem.get("text_style", {})
    align = tx_style.get("align", "left")
    valign = tx_style.get("vertical_align", "top")

    vert_anchor_map = {"top": "t", "middle": "ctr", "bottom": "b"}
    vert_anchor = vert_anchor_map.get(valign, "t")

    p_xml = build_paragraphs_xml(ctx, paragraphs, tx_style, align)

    bg_color = (elem.get("background") or {}).get("color")
    fill_xml = build_solid_fill_xml(bg_color, opacity) if bg_color else "<a:noFill/>"
    line_xml = build_line_xml(elem.get("border"))

    xfrm_xml = _build_xfrm_xml(x, y, cx, cy, rotation)

    return f'''
        <p:sp>
          <p:nvSpPr>
            <p:cNvPr id="{shape_id}" name="{name}"/>
            <p:cNvSpPr txBox="1"/>
            <p:nvPr/>
          </p:nvSpPr>
          <p:spPr>
            {xfrm_xml}
            <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
            {fill_xml}
            {line_xml}
          </p:spPr>
          <p:txBody>
            <a:bodyPr wrap="square" anchor="{vert_anchor}"/>
            <a:lstStyle/>
            {p_xml}
          </p:txBody>
        </p:sp>
        '''


def build_shape_xml(ctx: CompileContext, elem: Dict, shape_id: int) -> str:
    x, y, cx, cy = rect_px_to_emu(elem["bbox"], ctx.canvas_w, ctx.canvas_h, ctx.slide_w_emu, ctx.slide_h_emu)
    name = sanitize_xml_text(elem.get("name", elem.get("id", f"Shape {shape_id}")))
    prst = shape_type_to_ppt_prst(elem.get("shape", "rect"))
    rotation = elem.get("rotation", 0)
    opacity = elem.get("opacity", 1.0)

    fill_color = (elem.get("fill") or {}).get("color")
    fill_xml = build_solid_fill_xml(fill_color, opacity) if fill_color else "<a:noFill/>"
    line_xml = build_line_xml(elem.get("stroke"))

    xfrm_xml = _build_xfrm_xml(x, y, cx, cy, rotation)

    text_xml = ""
    if elem.get("text"):
        paragraphs = paragraphs_from_text_element(elem.get("text"))
        tx_style = elem.get("text_style", {})
        default_align = tx_style.get("align", "center")
        valign = tx_style.get("vertical_align", "middle")
        vert_anchor_map = {"top": "t", "middle": "ctr", "bottom": "b"}
        shape_anchor = vert_anchor_map.get(valign, "ctr")

        p_xml = build_paragraphs_xml(ctx, paragraphs, tx_style, default_align)

        text_xml = f'''
            <p:txBody>
              <a:bodyPr wrap="square" anchor="{shape_anchor}"/>
              <a:lstStyle/>
              {p_xml}
            </p:txBody>
            '''

    return f'''
        <p:sp>
          <p:nvSpPr>
            <p:cNvPr id="{shape_id}" name="{name}"/>
            <p:cNvSpPr/>
            <p:nvPr/>
          </p:nvSpPr>
          <p:spPr>
            {xfrm_xml}
            <a:prstGeom prst="{prst}"><a:avLst/></a:prstGeom>
            {fill_xml}
            {line_xml}
          </p:spPr>
          {text_xml}
        </p:sp>
        '''
