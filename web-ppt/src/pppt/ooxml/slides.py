from typing import Dict, List, Tuple

from ..constants import NS, REL_NS
from ..context import CompileContext
from ..xml_builders.shapes import build_textbox_xml, build_shape_xml
from ..xml_builders.pictures import build_picture_xml
from ..xml_builders.groups import build_group_xml
from ..xml_builders.tables import build_table_xml
from ..xml_builders.charts import build_chart_slide_xml, build_chart_file_xml
from ..xml_builders.backgrounds import build_slide_bg_xml
from ..xml_builders.transitions import build_transition_xml
from ..xml_builders.animations import build_timing_xml


def build_single_slide_xml(ctx: CompileContext, slide: Dict, slide_index: int) -> Tuple[str, str]:
    bg_xml = build_slide_bg_xml(ctx, slide)
    elements = slide.get("elements", [])
    elements_sorted = sorted(elements, key=lambda e: e.get("z_index", 0))

    shape_xml_parts = []
    rel_entries = [
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
    ]
    next_rel_id = 2
    shape_id = 2

    # Build element_id -> shape_id mapping for animations
    element_shape_map: Dict[str, int] = {}

    for elem in elements_sorted:
        etype = elem.get("type")
        elem_id = elem.get("id", "")

        if etype == "text":
            element_shape_map[elem_id] = shape_id
            shape_xml_parts.append(build_textbox_xml(ctx, elem, shape_id))
            shape_id += 1
        elif etype == "shape":
            element_shape_map[elem_id] = shape_id
            shape_xml_parts.append(build_shape_xml(ctx, elem, shape_id))
            shape_id += 1
        elif etype in ("image", "svg"):
            element_shape_map[elem_id] = shape_id
            pic_xml, rel_xml = build_picture_xml(ctx, elem, shape_id, next_rel_id)
            shape_xml_parts.append(pic_xml)
            rel_entries.append(rel_xml)
            next_rel_id += 1
            shape_id += 1
        elif etype == "group":
            element_shape_map[elem_id] = shape_id
            grp_xml, grp_rels, shape_id, next_rel_id = build_group_xml(
                ctx, elem, shape_id, next_rel_id, element_shape_map
            )
            shape_xml_parts.append(grp_xml)
            rel_entries.extend(grp_rels)
        elif etype == "table":
            element_shape_map[elem_id] = shape_id
            shape_xml_parts.append(build_table_xml(ctx, elem, shape_id))
            shape_id += 1
        elif etype == "chart":
            element_shape_map[elem_id] = shape_id
            chart_xml_content = build_chart_file_xml(ctx, elem)
            _chart_path, rel_target = ctx.asset_manager.add_chart(chart_xml_content)
            chart_frame_xml, rel_xml = build_chart_slide_xml(
                ctx, elem, shape_id, next_rel_id, rel_target
            )
            shape_xml_parts.append(chart_frame_xml)
            rel_entries.append(rel_xml)
            next_rel_id += 1
            shape_id += 1
        else:
            continue

    # Build transition XML
    timeline = slide.get("timeline")
    transition_xml = build_transition_xml(timeline)

    # Build animation timing XML
    animations = slide.get("animations", [])
    timing_xml = build_timing_xml(animations, element_shape_map)

    slide_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="{NS["a"]}" xmlns:r="{NS["r"]}" xmlns:p="{NS["p"]}">
  <p:cSld>
    {bg_xml}
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
      {''.join(shape_xml_parts)}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
  {transition_xml}
  {timing_xml}
</p:sld>
'''
    newline = "\n"
    rels_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{REL_NS}">
  {newline.join(rel_entries)}
</Relationships>
'''
    return slide_xml, rels_xml
