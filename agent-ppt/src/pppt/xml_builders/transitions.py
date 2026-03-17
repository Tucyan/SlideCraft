from typing import Dict, Optional


def build_transition_xml(timeline: Optional[Dict]) -> str:
    if not timeline:
        return ""

    transition = timeline.get("transition")
    auto_advance_ms = timeline.get("auto_advance_ms")

    if not transition and auto_advance_ms is None:
        return ""

    trans_type = (transition or {}).get("type", "none")
    duration_ms = (transition or {}).get("duration_ms", 500)
    direction = (transition or {}).get("direction")

    if trans_type == "none" and auto_advance_ms is None:
        return ""

    dir_map = {"left": "l", "right": "r", "top": "u", "bottom": "d"}

    # Build inner transition element
    inner_xml = ""
    if trans_type == "fade":
        inner_xml = "<p:fade/>"
    elif trans_type == "push":
        d = dir_map.get(direction, "l")
        inner_xml = f'<p:push dir="{d}"/>'
    elif trans_type == "wipe":
        d = dir_map.get(direction, "l")
        inner_xml = f'<p:wipe dir="{d}"/>'

    # Build transition attributes
    # spd must be enum ("slow"/"med"/"fast"), use dur (ms integer) for precise duration
    def _ms_to_spd(ms: int) -> str:
        if ms <= 300:
            return "fast"
        if ms <= 700:
            return "med"
        return "slow"

    attrs = ""
    if trans_type != "none":
        ms = int(duration_ms)
        attrs += f' spd="{_ms_to_spd(ms)}" dur="{ms}"'
    if auto_advance_ms is not None:
        attrs += f' advTm="{int(auto_advance_ms)}"'

    if not inner_xml and auto_advance_ms is None:
        return ""

    return f'<p:transition{attrs}>{inner_xml}</p:transition>'
