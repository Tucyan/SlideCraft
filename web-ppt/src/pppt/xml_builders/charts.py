from typing import Dict, Tuple

from ..constants import NS
from ..context import CompileContext
from ..utils import sanitize_xml_text, rect_px_to_emu, hex_to_rgb


CHART_NS = "http://schemas.openxmlformats.org/drawingml/2006/chart"

CHART_SERIES_PALETTE = ["4472C4", "ED7D31", "A5A5A5", "FFC000", "5B9BD5", "70AD47"]


def build_chart_slide_xml(
    ctx: CompileContext,
    elem: Dict,
    shape_id: int,
    rel_id_num: int,
    rel_target: str,
) -> Tuple[str, str]:
    """
    Build the <p:graphicFrame> that references an external chart file.

    Returns: (graphicFrame_xml, rel_entry_xml)
    """
    x, y, cx, cy = rect_px_to_emu(
        elem["bbox"], ctx.canvas_w, ctx.canvas_h, ctx.slide_w_emu, ctx.slide_h_emu
    )
    name = sanitize_xml_text(elem.get("name", elem.get("id", f"Chart {shape_id}")))
    rid = f"rId{rel_id_num}"

    frame_xml = f'''
        <p:graphicFrame>
          <p:nvGraphicFramePr>
            <p:cNvPr id="{shape_id}" name="{name}"/>
            <p:cNvGraphicFramePr><a:graphicFrameLocks noGrp="1"/></p:cNvGraphicFramePr>
            <p:nvPr/>
          </p:nvGraphicFramePr>
          <p:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></p:xfrm>
          <a:graphic>
            <a:graphicData uri="{CHART_NS}">
              <c:chart xmlns:c="{CHART_NS}" r:id="{rid}"/>
            </a:graphicData>
          </a:graphic>
        </p:graphicFrame>
        '''

    rel_xml = (
        f'<Relationship Id="{rid}"'
        f' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart"'
        f' Target="{rel_target}"/>'
    )

    return frame_xml, rel_xml


def build_chart_file_xml(ctx: CompileContext, elem: Dict) -> str:
    """
    Build the complete ppt/charts/chartN.xml file content.
    Uses inline literal data — no external Excel file required.
    """
    chart_type = elem.get("chart_type", "bar")
    title = elem.get("title")
    categories = elem.get("categories", [])
    series_list = elem.get("series", [])

    # Title XML
    if title:
        title_safe = sanitize_xml_text(str(title))
        title_xml = (
            f'<c:title>'
            f'<c:tx><c:rich>'
            f'<a:bodyPr/><a:lstStyle/>'
            f'<a:p><a:r><a:t>{title_safe}</a:t></a:r></a:p>'
            f'</c:rich></c:tx>'
            f'<c:overlay val="0"/>'
            f'</c:title>'
        )
    else:
        title_xml = '<c:autoTitleDeleted val="1"/>'

    # Series XML
    series_xml_parts = []
    n = len(categories)
    for idx, ser in enumerate(series_list):
        ser_name = sanitize_xml_text(str(ser.get("name", f"Series {idx + 1}")))
        values = ser.get("values", [])
        color = ser.get("color")
        color_rgb = hex_to_rgb(color) if color else CHART_SERIES_PALETTE[idx % len(CHART_SERIES_PALETTE)]

        # Categories (string literal)
        cat_pts = "".join(
            f'<c:pt idx="{i}"><c:v>{sanitize_xml_text(str(categories[i]))}</c:v></c:pt>'
            for i in range(n)
        )
        cat_xml = (
            f'<c:cat><c:strLit>'
            f'<c:ptCount val="{n}"/>'
            f'{cat_pts}'
            f'</c:strLit></c:cat>'
        )

        # Values (numeric literal)
        val_pts = "".join(
            f'<c:pt idx="{i}"><c:v>{values[i] if i < len(values) else 0}</c:v></c:pt>'
            for i in range(n)
        )
        val_xml = (
            f'<c:val><c:numLit>'
            f'<c:ptCount val="{n}"/>'
            f'{val_pts}'
            f'</c:numLit></c:val>'
        )

        color_xml = (
            f'<c:spPr><a:solidFill><a:srgbClr val="{color_rgb}"/></a:solidFill></c:spPr>'
        )

        series_xml_parts.append(
            f'<c:ser>'
            f'<c:idx val="{idx}"/><c:order val="{idx}"/>'
            f'<c:tx><c:v>{ser_name}</c:v></c:tx>'
            f'{color_xml}'
            f'{cat_xml}'
            f'{val_xml}'
            f'</c:ser>'
        )

    ser_xml = "".join(series_xml_parts)

    # Axis definitions (required for bar/line charts)
    CAT_AX_ID = "64272128"
    VAL_AX_ID = "64274560"
    ax_ids = f'<c:axId val="{CAT_AX_ID}"/><c:axId val="{VAL_AX_ID}"/>'
    axes_xml = (
        f'<c:catAx>'
        f'<c:axId val="{CAT_AX_ID}"/>'
        f'<c:scaling><c:orientation val="minMax"/></c:scaling>'
        f'<c:delete val="0"/>'
        f'<c:axPos val="b"/>'
        f'<c:crossAx val="{VAL_AX_ID}"/>'
        f'</c:catAx>'
        f'<c:valAx>'
        f'<c:axId val="{VAL_AX_ID}"/>'
        f'<c:scaling><c:orientation val="minMax"/></c:scaling>'
        f'<c:delete val="0"/>'
        f'<c:axPos val="l"/>'
        f'<c:crossAx val="{CAT_AX_ID}"/>'
        f'</c:valAx>'
    )

    # Chart body by type
    if chart_type == "bar":
        chart_body = (
            f'<c:barChart>'
            f'<c:barDir val="col"/><c:grouping val="clustered"/>'
            f'{ser_xml}'
            f'{ax_ids}'
            f'</c:barChart>'
            f'{axes_xml}'
        )
    elif chart_type == "bar_horizontal":
        chart_body = (
            f'<c:barChart>'
            f'<c:barDir val="bar"/><c:grouping val="clustered"/>'
            f'{ser_xml}'
            f'{ax_ids}'
            f'</c:barChart>'
            f'{axes_xml}'
        )
    elif chart_type == "line":
        chart_body = (
            f'<c:lineChart>'
            f'<c:grouping val="standard"/>'
            f'{ser_xml}'
            f'{ax_ids}'
            f'</c:lineChart>'
            f'{axes_xml}'
        )
    elif chart_type == "pie":
        chart_body = f'<c:pieChart>{ser_xml}</c:pieChart>'
    else:
        # Default to bar
        chart_body = (
            f'<c:barChart>'
            f'<c:barDir val="col"/><c:grouping val="clustered"/>'
            f'{ser_xml}'
            f'{ax_ids}'
            f'</c:barChart>'
            f'{axes_xml}'
        )

    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<c:chartSpace'
        f' xmlns:c="{CHART_NS}"'
        f' xmlns:a="{NS["a"]}"'
        f' xmlns:r="{NS["r"]}">'
        f'<c:lang val="{ctx.language}"/>'
        f'<c:chart>'
        f'{title_xml}'
        f'<c:plotArea>{chart_body}</c:plotArea>'
        f'<c:legend><c:legendPos val="b"/></c:legend>'
        f'<c:plotVisOnly val="1"/>'
        f'</c:chart>'
        f'</c:chartSpace>'
    )
