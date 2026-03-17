from typing import Dict, Tuple

from ..context import CompileContext
from ..utils import sanitize_xml_text, rect_px_to_emu


def build_picture_xml(ctx: CompileContext, elem: Dict, shape_id: int, rel_id_num: int) -> Tuple[str, str]:
    asset_id = elem.get("asset_id")
    if not asset_id:
        raise ValueError(f'Element {elem.get("id")} missing asset_id')

    asset = ctx.assets.get(asset_id)
    if not asset:
        raise ValueError(f'Asset not found: {asset_id}')

    bbox = elem["bbox"]
    fit = elem.get("fit", "contain")
    box_w = max(1, int(bbox["w"]))
    box_h = max(1, int(bbox["h"]))
    rotation = elem.get("rotation", 0)
    opacity = elem.get("opacity", 1.0)

    media_name, _ = ctx.asset_manager.materialize_asset_image(
        asset=asset,
        fit_mode=fit,
        target_w_px=box_w,
        target_h_px=box_h
    )

    x, y, cx, cy = rect_px_to_emu(bbox, ctx.canvas_w, ctx.canvas_h, ctx.slide_w_emu, ctx.slide_h_emu)
    name = sanitize_xml_text(elem.get("name", elem.get("id", f"Picture {shape_id}")))
    rid = f"rId{rel_id_num}"

    rot_attr = f' rot="{int(rotation * 60000)}"' if rotation else ""

    # Opacity for images: alphaModFix inside blip
    alpha_mod_xml = ""
    if opacity < 1.0:
        amt = int(opacity * 100000)
        alpha_mod_xml = f'<a:alphaModFix amt="{amt}"/>'

    blip_children = alpha_mod_xml
    if blip_children:
        blip_xml = f'<a:blip r:embed="{rid}">{blip_children}</a:blip>'
    else:
        blip_xml = f'<a:blip r:embed="{rid}"/>'

    pic_xml = f'''
        <p:pic>
          <p:nvPicPr>
            <p:cNvPr id="{shape_id}" name="{name}"/>
            <p:cNvPicPr/>
            <p:nvPr/>
          </p:nvPicPr>
          <p:blipFill>
            {blip_xml}
            <a:stretch><a:fillRect/></a:stretch>
          </p:blipFill>
          <p:spPr>
            <a:xfrm{rot_attr}>
              <a:off x="{x}" y="{y}"/>
              <a:ext cx="{cx}" cy="{cy}"/>
            </a:xfrm>
            <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
          </p:spPr>
        </p:pic>
        '''

    rel_xml = f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/{media_name}"/>'
    return pic_xml, rel_xml
