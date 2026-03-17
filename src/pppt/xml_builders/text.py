from typing import Dict, List

from ..context import CompileContext
from ..utils import sanitize_xml_text, hex_to_rgb


def build_paragraphs_xml(ctx: CompileContext, paragraphs: List[Dict], text_style: Dict, default_align: str = "left") -> str:
    default_font = sanitize_xml_text(text_style.get("font_family", ctx.theme.get("font_scheme", {}).get("body_font", "Microsoft YaHei")))
    default_size = int(text_style.get("font_size", 20) * 100)
    default_color = hex_to_rgb(text_style.get("color", "#000000"))

    p_xml = []
    for p in paragraphs:
        palign = p.get("align", default_align)
        align_map = {
            "left": "l",
            "center": "ctr",
            "right": "r",
            "justify": "just"
        }
        ppt_align = align_map.get(palign, "l")

        bullet = p.get("bullet")
        bullet_xml = ""
        if bullet:
            btype = bullet.get("type")
            if btype == "disc":
                bullet_xml = "<a:buChar char='\u2022'/>"
            elif btype == "dash":
                bullet_xml = "<a:buChar char='\u2013'/>"
            elif btype == "number":
                start_at = int(bullet.get("start_at", 1))
                bullet_xml = f'<a:buAutoNum type="arabicPeriod" startAt="{start_at}"/>'

        runs_xml = []
        for run in p.get("runs", []):
            text = sanitize_xml_text(run.get("text", ""))
            r_font = sanitize_xml_text(run.get("font_family", default_font))
            r_size = int(run.get("font_size", default_size // 100) * 100)
            r_color = hex_to_rgb(run.get("color", f"#{default_color}"), default_color)

            bold = ' b="1"' if run.get("bold") else ""
            italic = ' i="1"' if run.get("italic") else ""
            underline = ' u="sng"' if run.get("underline") else ""

            runs_xml.append(f'''
                <a:r>
                  <a:rPr lang="{ctx.language}" sz="{r_size}"{bold}{italic}{underline} dirty="0" smtClean="0">
                    <a:solidFill><a:srgbClr val="{r_color}"/></a:solidFill>
                    <a:latin typeface="{r_font}"/>
                    <a:ea typeface="{r_font}"/>
                    <a:cs typeface="{r_font}"/>
                  </a:rPr>
                  <a:t>{text}</a:t>
                </a:r>
                ''')

        if not runs_xml:
            runs_xml.append(f"<a:endParaRPr lang='{ctx.language}'/>")

        p_xml.append(f'''
            <a:p>
              <a:pPr algn="{ppt_align}">{bullet_xml}</a:pPr>
              {''.join(runs_xml)}
              <a:endParaRPr lang="{ctx.language}" sz="{default_size}"/>
            </a:p>
            ''')

    return ''.join(p_xml)
