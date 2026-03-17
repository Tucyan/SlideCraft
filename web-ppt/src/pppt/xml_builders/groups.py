from typing import Dict, List, Tuple

from ..context import CompileContext
from ..utils import sanitize_xml_text, rect_px_to_emu
from .shapes import build_textbox_xml, build_shape_xml
from .pictures import build_picture_xml


def build_group_xml(
    ctx: CompileContext,
    elem: Dict,
    shape_id: int,
    next_rel_id: int,
    element_shape_map: Dict[str, int],
) -> Tuple[str, List[str], int, int]:
    """
    Build a <p:grpSp> XML element.

    Children bbox coords are relative to the group origin; this function
    converts them to absolute canvas coordinates before passing to builders.

    Returns: (grpSp_xml, rel_entries_list, final_shape_id, final_rel_id)
    final_shape_id = next available shape_id after group + all children
    """
    group_shape_id = shape_id
    shape_id += 1

    x, y, cx, cy = rect_px_to_emu(
        elem["bbox"], ctx.canvas_w, ctx.canvas_h, ctx.slide_w_emu, ctx.slide_h_emu
    )
    name = sanitize_xml_text(elem.get("name", elem.get("id", f"Group {group_shape_id}")))
    rotation = elem.get("rotation", 0)
    rot_attr = f' rot="{int(rotation * 60000)}"' if rotation else ""

    group_bbox = elem.get("bbox", {"x": 0, "y": 0, "w": 0, "h": 0})
    children = elem.get("children", [])
    children_sorted = sorted(children, key=lambda c: c.get("z_index", 0))

    children_xml_parts = []
    rel_entries = []

    for child in children_sorted:
        child_id = child.get("id", "")
        child_bbox = child.get("bbox", {"x": 0, "y": 0, "w": 0, "h": 0})
        abs_bbox = {
            "x": group_bbox["x"] + child_bbox["x"],
            "y": group_bbox["y"] + child_bbox["y"],
            "w": child_bbox["w"],
            "h": child_bbox["h"],
        }
        child_abs = {**child, "bbox": abs_bbox}
        ctype = child.get("type")

        if child_id:
            element_shape_map[child_id] = shape_id

        if ctype == "text":
            children_xml_parts.append(build_textbox_xml(ctx, child_abs, shape_id))
            shape_id += 1
        elif ctype == "shape":
            children_xml_parts.append(build_shape_xml(ctx, child_abs, shape_id))
            shape_id += 1
        elif ctype in ("image", "svg"):
            child_xml, rel_xml = build_picture_xml(ctx, child_abs, shape_id, next_rel_id)
            children_xml_parts.append(child_xml)
            rel_entries.append(rel_xml)
            next_rel_id += 1
            shape_id += 1
        elif ctype == "group":
            child_grp_xml, child_rels, shape_id, next_rel_id = build_group_xml(
                ctx, child_abs, shape_id, next_rel_id, element_shape_map
            )
            children_xml_parts.append(child_grp_xml)
            rel_entries.extend(child_rels)

    grpSp_xml = f'''
        <p:grpSp>
          <p:nvGrpSpPr>
            <p:cNvPr id="{group_shape_id}" name="{name}"/>
            <p:cNvGrpSpPr/>
            <p:nvPr/>
          </p:nvGrpSpPr>
          <p:grpSpPr>
            <a:xfrm{rot_attr}>
              <a:off x="{x}" y="{y}"/>
              <a:ext cx="{cx}" cy="{cy}"/>
              <a:chOff x="{x}" y="{y}"/>
              <a:chExt cx="{cx}" cy="{cy}"/>
            </a:xfrm>
          </p:grpSpPr>
          {''.join(children_xml_parts)}
        </p:grpSp>
        '''

    return grpSp_xml, rel_entries, shape_id, next_rel_id
