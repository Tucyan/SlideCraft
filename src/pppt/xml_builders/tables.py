from typing import Dict

from ..context import CompileContext
from ..utils import sanitize_xml_text, rect_px_to_emu, px_to_emu_x, px_to_emu_y, hex_to_rgb
from .text import build_paragraphs_xml
from .common import build_solid_fill_xml


def _build_border_line(tag: str, w_emu: int, color_rgb: str) -> str:
    """Build a border line element (<a:lnL>, <a:lnR>, <a:lnT>, <a:lnB>)."""
    if w_emu > 0:
        return (
            f'<a:{tag} w="{w_emu}">'
            f'<a:solidFill><a:srgbClr val="{color_rgb}"/></a:solidFill>'
            f'</a:{tag}>'
        )
    return f'<a:{tag}><a:noFill/></a:{tag}>'


def build_table_xml(ctx: CompileContext, elem: Dict, shape_id: int) -> str:
    """
    Build a <p:graphicFrame> containing an <a:tbl> table element.
    Returns the XML string (no rel entries needed; data is inline).
    """
    x, y, cx, cy = rect_px_to_emu(
        elem["bbox"], ctx.canvas_w, ctx.canvas_h, ctx.slide_w_emu, ctx.slide_h_emu
    )
    name = sanitize_xml_text(elem.get("name", elem.get("id", f"Table {shape_id}")))

    rows = elem.get("rows", 1)
    cols = elem.get("cols", 1)
    bbox_w = elem["bbox"].get("w", 0)
    bbox_h = elem["bbox"].get("h", 0)

    # Column widths
    col_widths_px = elem.get("column_widths", [])
    if not col_widths_px or len(col_widths_px) != cols:
        col_w = bbox_w / cols if cols > 0 else bbox_w
        col_widths_px = [col_w] * cols

    # Row heights
    row_heights_px = elem.get("row_heights", [])
    if not row_heights_px or len(row_heights_px) != rows:
        row_h = bbox_h / rows if rows > 0 else bbox_h
        row_heights_px = [row_h] * rows

    col_widths_emu = [px_to_emu_x(w, ctx.canvas_w, ctx.slide_w_emu) for w in col_widths_px]
    row_heights_emu = [px_to_emu_y(h, ctx.canvas_h, ctx.slide_h_emu) for h in row_heights_px]

    # Build cell lookup map
    cells_data = elem.get("cells", [])
    cell_map = {}
    for cell in cells_data:
        r = cell.get("row", 0)
        c = cell.get("col", 0)
        cell_map[(r, c)] = cell

    # Borders
    borders = elem.get("borders")
    border_w_emu = 0
    border_color_rgb = "CCCCCC"
    if borders:
        border_w_emu = int(float(borders.get("width", 1)) * 12700)
        border_color_rgb = hex_to_rgb(borders.get("color", "#CCCCCC"))

    # tblGrid
    grid_xml = "\n".join(f'<a:gridCol w="{w}"/>' for w in col_widths_emu)

    # Build rows
    rows_xml_parts = []
    for r in range(rows):
        row_h_emu = row_heights_emu[r] if r < len(row_heights_emu) else row_heights_emu[-1]
        cells_xml_parts = []

        for c in range(cols):
            cell = cell_map.get((r, c), {})
            fill_color = cell.get("fill_color")
            text_block = cell.get("text") or {}
            text_style = cell.get("text_style") or {}

            paragraphs = text_block.get("paragraphs", [])
            if not paragraphs:
                paragraphs = [{"runs": [{"text": ""}]}]

            default_align = text_style.get("align", "left")
            valign = text_style.get("vertical_align", "top")
            vert_anchor_map = {"top": "t", "middle": "ctr", "bottom": "b"}
            anchor = vert_anchor_map.get(valign, "t")

            p_xml = build_paragraphs_xml(ctx, paragraphs, text_style, default_align)

            fill_xml = build_solid_fill_xml(fill_color) if fill_color else "<a:noFill/>"

            # Build border lines (must come before fill in <a:tcPr>)
            border_xml = ""
            if borders:
                border_xml = (
                    _build_border_line("lnL", border_w_emu, border_color_rgb)
                    + _build_border_line("lnR", border_w_emu, border_color_rgb)
                    + _build_border_line("lnT", border_w_emu, border_color_rgb)
                    + _build_border_line("lnB", border_w_emu, border_color_rgb)
                )

            tc_xml = (
                f'<a:tc>'
                f'<a:txBody><a:bodyPr/><a:lstStyle/>{p_xml}</a:txBody>'
                f'<a:tcPr anchor="{anchor}">{border_xml}{fill_xml}</a:tcPr>'
                f'</a:tc>'
            )
            cells_xml_parts.append(tc_xml)

        rows_xml_parts.append(
            f'<a:tr h="{row_h_emu}">{"".join(cells_xml_parts)}</a:tr>'
        )

    return f'''
        <p:graphicFrame>
          <p:nvGraphicFramePr>
            <p:cNvPr id="{shape_id}" name="{name}"/>
            <p:cNvGraphicFramePr><a:graphicFrameLocks noGrp="1"/></p:cNvGraphicFramePr>
            <p:nvPr/>
          </p:nvGraphicFramePr>
          <p:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></p:xfrm>
          <a:graphic>
            <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table">
              <a:tbl>
                <a:tblPr firstRow="1" bandRow="1">
                  <a:tableStyleId>{{00000000-0000-0000-0000-000000000000}}</a:tableStyleId>
                </a:tblPr>
                <a:tblGrid>
                  {grid_xml}
                </a:tblGrid>
                {''.join(rows_xml_parts)}
              </a:tbl>
            </a:graphicData>
          </a:graphic>
        </p:graphicFrame>
        '''
