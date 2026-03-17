from typing import Optional, Dict, List

from ..utils import hex_to_rgb


def build_solid_fill_xml(color: Optional[str], opacity: float = 1.0) -> str:
    if not color:
        return "<a:noFill/>"
    rgb = hex_to_rgb(color)
    if opacity < 1.0:
        alpha_val = int(opacity * 100000)
        return f'<a:solidFill><a:srgbClr val="{rgb}"><a:alpha val="{alpha_val}"/></a:srgbClr></a:solidFill>'
    return f'<a:solidFill><a:srgbClr val="{rgb}"/></a:solidFill>'


def build_gradient_fill_xml(gradient: Dict) -> str:
    angle = int(gradient.get("angle", 90) * 60000)
    stops = gradient.get("stops", [])
    gs_parts = []
    for stop in stops:
        pos = int(float(stop.get("offset", 0)) * 100000)
        color = hex_to_rgb(stop.get("color", "#000000"))
        stop_opacity = stop.get("opacity", 1.0)
        if stop_opacity < 1.0:
            alpha_val = int(stop_opacity * 100000)
            gs_parts.append(f'<a:gs pos="{pos}"><a:srgbClr val="{color}"><a:alpha val="{alpha_val}"/></a:srgbClr></a:gs>')
        else:
            gs_parts.append(f'<a:gs pos="{pos}"><a:srgbClr val="{color}"/></a:gs>')

    return f'''<a:gradFill>
  <a:gsLst>
    {''.join(gs_parts)}
  </a:gsLst>
  <a:lin ang="{angle}" scaled="0"/>
</a:gradFill>'''


def build_line_xml(stroke: Optional[Dict]) -> str:
    if not stroke:
        return "<a:ln><a:noFill/></a:ln>"

    color = hex_to_rgb(stroke.get("color", "#000000"))
    width = int(float(stroke.get("width", 1)) * 12700)
    return f'''
    <a:ln w="{width}">
      <a:solidFill><a:srgbClr val="{color}"/></a:solidFill>
    </a:ln>
    '''
