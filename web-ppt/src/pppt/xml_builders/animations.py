from typing import Dict, List


# Animation type to OOXML preset mapping
ANIM_PRESETS = {
    "appear":         {"class": "entr", "id": 1},
    "fade":           {"class": "entr", "id": 10},
    "fly_in":         {"class": "entr", "id": 2},
    "zoom":           {"class": "entr", "id": 53},
    "wipe":           {"class": "entr", "id": 22},
    "emphasis_pulse": {"class": "emph", "id": 26},
    "exit_fade":      {"class": "exit", "id": 10},
}

# fly_in direction -> presetSubtype
FLY_IN_SUBTYPES = {"bottom": 4, "top": 8, "left": 2, "right": 1}
# wipe direction -> presetSubtype
WIPE_SUBTYPES = {"left": 1, "right": 2, "top": 4, "bottom": 8}


def _build_anim_behavior_xml(anim: Dict, shape_id: int) -> str:
    """Build the inner behavior XML node for one animation."""
    anim_type = anim.get("type", "appear")
    direction = anim.get("direction", "bottom")
    duration_ms = anim.get("duration_ms", 500)
    dur = str(duration_ms)

    if anim_type == "appear":
        return f'''<p:set>
              <p:cBhvr>
                <p:cTn id="{{tn_id}}" dur="1" fill="hold">
                  <p:stCondLst><p:cond delay="0"/></p:stCondLst>
                </p:cTn>
                <p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>
                <p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst>
              </p:cBhvr>
              <p:to><p:strVal val="visible"/></p:to>
            </p:set>'''

    if anim_type == "fade":
        return f'''<p:animEffect transition="in" filter="fade">
              <p:cBhvr>
                <p:cTn id="{{tn_id}}" dur="{dur}" fill="hold"/>
                <p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>
              </p:cBhvr>
            </p:animEffect>'''

    if anim_type == "exit_fade":
        return f'''<p:animEffect transition="out" filter="fade">
              <p:cBhvr>
                <p:cTn id="{{tn_id}}" dur="{dur}" fill="hold"/>
                <p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>
              </p:cBhvr>
            </p:animEffect>'''

    if anim_type == "fly_in":
        # Animate position from offscreen
        axis_map = {"bottom": "ppt_y", "top": "ppt_y", "left": "ppt_x", "right": "ppt_x"}
        axis = axis_map.get(direction, "ppt_y")
        # Start value: offscreen position (1 = 100% offscreen for bottom/right, -1 for top/left)
        # Use #ppt_h for vertical (top/bottom), #ppt_w for horizontal (left/right)
        if direction in ("bottom", "top"):
            size_var = "#ppt_h"
        else:
            size_var = "#ppt_w"

        if direction in ("bottom", "right"):
            from_val = f"1+{size_var}/2"
        else:
            from_val = f"-1-{size_var}/2"

        # End value must match the animated axis
        end_val = f"#{axis}"

        return f'''<p:anim calcmode="lin" valueType="num">
              <p:cBhvr additive="base">
                <p:cTn id="{{tn_id}}" dur="{dur}" fill="hold"/>
                <p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>
                <p:attrNameLst><p:attrName>{axis}</p:attrName></p:attrNameLst>
              </p:cBhvr>
              <p:tavLst>
                <p:tav tm="0"><p:val><p:strVal val="{from_val}"/></p:val></p:tav>
                <p:tav tm="100000"><p:val><p:strVal val="{end_val}"/></p:val></p:tav>
              </p:tavLst>
            </p:anim>'''

    if anim_type == "zoom":
        return f'''<p:animScale>
              <p:cBhvr>
                <p:cTn id="{{tn_id}}" dur="{dur}" fill="hold"/>
                <p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>
              </p:cBhvr>
              <p:from x="0" y="0"/>
              <p:to x="100000" y="100000"/>
            </p:animScale>'''

    if anim_type == "wipe":
        wipe_dir_map = {"left": "wipe(left)", "right": "wipe(right)", "top": "wipe(up)", "bottom": "wipe(down)"}
        filt = wipe_dir_map.get(direction, "wipe(left)")
        return f'''<p:animEffect transition="in" filter="{filt}">
              <p:cBhvr>
                <p:cTn id="{{tn_id}}" dur="{dur}" fill="hold"/>
                <p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>
              </p:cBhvr>
            </p:animEffect>'''

    if anim_type == "emphasis_pulse":
        return f'''<p:animScale>
              <p:cBhvr>
                <p:cTn id="{{tn_id}}" dur="{dur}" autoReverse="1" fill="hold" repeatCount="2000"/>
                <p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>
              </p:cBhvr>
              <p:by x="105000" y="105000"/>
            </p:animScale>'''

    # Fallback: appear
    return f'''<p:set>
              <p:cBhvr>
                <p:cTn id="{{tn_id}}" dur="1" fill="hold">
                  <p:stCondLst><p:cond delay="0"/></p:stCondLst>
                </p:cTn>
                <p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>
                <p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst>
              </p:cBhvr>
              <p:to><p:strVal val="visible"/></p:to>
            </p:set>'''


def build_timing_xml(animations: List[Dict], element_shape_map: Dict[str, int]) -> str:
    """Build the <p:timing> XML block for slide animations.

    Args:
        animations: list of animation dicts from the JSON
        element_shape_map: mapping of element_id -> shape_id (OOXML sp id)
    """
    if not animations:
        return ""

    # Sort by order
    sorted_anims = sorted(animations, key=lambda a: a.get("order", 0))

    # Group animations into click sequences
    # on_click starts a new click sequence
    # with_previous and after_previous attach to current sequence
    click_groups: List[List[Dict]] = []
    current_group: List[Dict] = []

    for anim in sorted_anims:
        trigger = anim.get("trigger", "on_click")
        if trigger == "on_click" and current_group:
            click_groups.append(current_group)
            current_group = [anim]
        else:
            current_group.append(anim)

    if current_group:
        click_groups.append(current_group)

    # We need a global tn_id counter
    tn_id = [1]  # Use list for mutability in nested function

    def next_tn():
        val = tn_id[0]
        tn_id[0] += 1
        return val

    # Build the main sequence node children
    seq_children = []
    # Track shape IDs that have entrance animations (need bldLst for initial hide)
    entrance_shape_ids = set()

    for group_idx, group in enumerate(click_groups):
        # Each click group is a <p:seq> child node (ctNode in the tnLst)
        # We create a par for each group

        par_children = []
        for anim in group:
            target_id = anim.get("target_id")
            shape_id = element_shape_map.get(target_id)
            if shape_id is None:
                continue

            anim_type = anim.get("type", "appear")
            direction = anim.get("direction", "bottom")
            delay_ms = anim.get("delay_ms", 0)
            duration_ms = anim.get("duration_ms", 500)
            trigger = anim.get("trigger", "on_click")

            preset = ANIM_PRESETS.get(anim_type, {"class": "entr", "id": 1})
            preset_class = preset["class"]
            preset_id = preset["id"]

            # Track entrance animations for bldLst
            if preset_class == "entr":
                entrance_shape_ids.add(shape_id)

            # Determine presetSubtype (always output, even when 0)
            preset_subtype = 0
            if anim_type == "fly_in":
                preset_subtype = FLY_IN_SUBTYPES.get(direction, 4)
            elif anim_type == "wipe":
                preset_subtype = WIPE_SUBTYPES.get(direction, 1)

            subtype_attr = f' presetSubtype="{preset_subtype}"'

            # Entrance animations need grpId to link with bldLst
            grp_id_attr = ' grpId="0"' if preset_class == "entr" else ""

            # Build behavior node
            behavior_xml = _build_anim_behavior_xml(anim, shape_id)

            # Determine the start condition based on trigger.
            # MS Office uses nodeType="afterEffect" to determine sequencing;
            # the delay value is interpreted as "delay after previous animation ends".
            if trigger == "on_click":
                start_cond = '<p:stCondLst><p:cond delay="0"/></p:stCondLst>'
            elif trigger == "with_previous":
                start_cond = '<p:stCondLst><p:cond delay="0"/></p:stCondLst>'
            else:  # after_previous
                start_cond = f'<p:stCondLst><p:cond delay="{delay_ms}"/></p:stCondLst>'

            inner_tn = next_tn()

            # For entrance animations (except "appear" which is already a <p:set>),
            # prepend a <p:set> visibility="visible" node. This works with <p:bldLst>:
            #   bldLst hides the shape initially, then this <p:set> makes it visible
            #   when the entrance animation fires.
            visibility_set_xml = ""
            if preset_class == "entr" and anim_type != "appear":
                vis_tn = next_tn()
                visibility_set_xml = f'''<p:set>
                    <p:cBhvr>
                      <p:cTn id="{vis_tn}" dur="1" fill="hold">
                        <p:stCondLst><p:cond delay="0"/></p:stCondLst>
                      </p:cTn>
                      <p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>
                      <p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst>
                    </p:cBhvr>
                    <p:to><p:strVal val="visible"/></p:to>
                  </p:set>'''

            # Wrap in a par node
            node_type = "clickEffect" if trigger == "on_click" else ("withEffect" if trigger == "with_previous" else "afterEffect")
            anim_par = f'''<p:par>
              <p:cTn id="{inner_tn}" presetID="{preset_id}" presetClass="{preset_class}"{subtype_attr}{grp_id_attr} fill="hold" nodeType="{node_type}">
                {start_cond}
                <p:childTnLst>
                  {visibility_set_xml}{behavior_xml.format(tn_id=next_tn())}
                </p:childTnLst>
              </p:cTn>
            </p:par>'''

            par_children.append(anim_par)

        if not par_children:
            continue

        # Wrap all pars for this group in a top-level par
        # If the first animation in this group has on_click trigger,
        # set delay="indefinite" so PowerPoint waits for a click.
        # Otherwise delay="0" for auto-play (with_previous / after_previous).
        first_trigger = group[0].get("trigger", "on_click")
        group_delay = "indefinite" if first_trigger == "on_click" else "0"

        group_tn = next_tn()
        group_par = f'''<p:par>
          <p:cTn id="{group_tn}" fill="hold">
            <p:stCondLst><p:cond delay="{group_delay}"/></p:stCondLst>
            <p:childTnLst>
              {''.join(par_children)}
            </p:childTnLst>
          </p:cTn>
        </p:par>'''

        seq_children.append(group_par)

    if not seq_children:
        return ""

    # Build the main sequence
    main_seq_tn = next_tn()
    root_tn = next_tn()

    main_seq = f'''<p:seq concurrent="1" nextAc="seek">
      <p:cTn id="{main_seq_tn}" dur="indefinite" nodeType="mainSeq">
        <p:childTnLst>
          {''.join(seq_children)}
        </p:childTnLst>
      </p:cTn>
      <p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>
      <p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>
    </p:seq>'''

    # Build bldLst for entrance animations (tells PowerPoint to hide these shapes initially)
    bld_lst_xml = ""
    if entrance_shape_ids:
        bld_entries = ''.join(
            f'<p:bldP spid="{sid}" grpId="0" animBg="1"/>'
            for sid in sorted(entrance_shape_ids)
        )
        bld_lst_xml = f'\n    <p:bldLst>{bld_entries}</p:bldLst>'

    return f'''<p:timing>
    <p:tnLst>
      <p:par>
        <p:cTn id="{root_tn}" dur="indefinite" restart="never" nodeType="tmRoot">
          <p:childTnLst>
            {main_seq}
          </p:childTnLst>
        </p:cTn>
      </p:par>
    </p:tnLst>{bld_lst_xml}
  </p:timing>'''
