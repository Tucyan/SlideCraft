# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PPPT** (JSON → PPTX via Open XML) is a compiler that converts structured JSON presentations into PowerPoint files.

- Input: JSON following the spec in `llm_prompt.md`
- Output: Valid PPTX files (Office Open XML format)
- Supported features: text, shapes, images, SVG (via cairosvg), groups, tables, charts, rotations, opacity, gradients, transitions, animations

Current version: **0.3.2** (animation compatibility fixes)

---

## Architecture: Three-Layer Design

### Layer 1: CompileContext (`src/pppt/context.py`)

Central dataclass passed through all XML builders. Contains:
- Canvas dimensions (pixels) + Slide dimensions (EMU units)
- Language setting
- Theme, assets, asset manager
- Controls coordinate transformation and resource loading

**Why this pattern?** Avoids scattered state across exporter methods; enables pure functional XML builders.

### Layer 2: XML Builders (`src/pppt/xml_builders/`)

Pure functions that generate Open XML fragments. Each receives `CompileContext` plus element data.

**Key modules:**
- `common.py` — fill/stroke/gradient XML (with opacity support)
- `text.py` — paragraph rendering (shared between textbox, shape, table cell)
- `shapes.py` — shape/textbox XML (with rotation via `rot` attribute)
- `pictures.py` — image embedding (with alphaModFix for opacity)
- `groups.py` — group element XML (`<p:grpSp>`); recursively dispatches children; converts child bbox from group-relative to absolute canvas coords
- `tables.py` — table XML (`<p:graphicFrame>/<a:tbl>`); cell text reuses `build_paragraphs_xml`; borders use lnL/lnR/lnT/lnB
- `charts.py` — chart XML; `build_chart_slide_xml()` generates the slide's `<p:graphicFrame>` referencing an external chart file; `build_chart_file_xml()` generates the standalone `ppt/charts/chartN.xml` with inline data
- `backgrounds.py` — slide backgrounds (color + gradient)
- `transitions.py` — slide transitions (fade/push/wipe + auto_advance) — **Note:** `spd` is enum ("slow"/"med"/"fast"), not numeric
- `animations.py` — complex timing XML generation (see "Animation Complexity" below)

### Layer 3: OOXML Package (`src/pppt/ooxml/`)

Writes static OOXML files (presentation.xml, theme, slideMaster, etc.) and assembles slides into a ZIP.

**Key entry point:** `ooxml/slides.py:build_single_slide_xml()` — orchestrates element→shape_id mapping for animations, then stitches together background, shapes, transitions, timing into slide XML. Dispatches all seven element types: text, shape, image, svg, group, table, chart.

---

## Common Commands

### Run Tests (15 tests, ~1s)

```bash
cd /c/Users/ALmerb/Desktop/MyProgram/important/pppt
PYTHONPATH=src .venv/Scripts/python.exe -m pytest tests/ -v
```

Single test:

```bash
PYTHONPATH=src .venv/Scripts/python.exe -m pytest tests/test_exporter.py::test_exporter_creates_pptx -v
```

### Generate PPTX (bash/PowerShell)

**Bash:**
```bash
PYTHONPATH=src .venv/Scripts/python.exe -m pppt.cli input.json -o output.pptx
```

**PowerShell:**
```powershell
$env:PYTHONPATH = "src"
.venv\Scripts\python.exe -m pppt.cli input.json -o output.pptx
```

### Entry Points

- `pppt.cli:main()` — Recommended CLI entry, reads JSON + outputs PPTX
- `demo.py` — Backward-compatible wrapper (for legacy callers)
- `JsonToPptxExporter(doc, output_path)` — Programmatic API (pass parsed dict)
- `JsonToPptxExporter.from_json_file(json_path, output_path)` — Convenience static method (reads JSON file)

---

## Key Design Decisions & Gotchas

### EMU (English Metric Units)

PowerPoint uses EMU internally; PPPT converts pixel coordinates to EMU using:
- `canvas_to_slide_emu(width_px, height_px)` → slide dimensions in EMU
- `rect_px_to_emu(rect, canvas_w, canvas_h, slide_w_emu, slide_h_emu)` → element bounds in EMU

**Important:** Must pass `slide_w_emu/slide_h_emu` to conversion functions — they can't assume 16:9 dimensions.

### Group Element Coordinate System

`<p:grpSp>` uses a two-coordinate-system model:
- `<a:off>` / `<a:ext>` — group's position/size in the parent (slide) space
- `<a:chOff>` / `<a:chExt>` — origin and extent of the child coordinate system

**PPPT's approach:** Set `chOff = off` and `chExt = ext`. Children use absolute slide coordinates (group-relative bbox is converted to absolute by adding group's x/y before passing to child builders). This keeps child builders stateless and reusable.

**Group opacity:** `<p:grpSp>` has no direct opacity attribute in OOXML. Opacity must be set on individual child elements.

**Group animation:** The group's `shape_id` is registered in `element_shape_map` so animations can target the whole group. Each child's `id` is also registered individually, enabling per-child animations.

### Table Element Structure

`<a:tcPr>` child element ordering is enforced by OOXML schema:
1. Border lines (`lnL`, `lnR`, `lnT`, `lnB`) — **must come before fill**
2. Fill (`solidFill`, `noFill`, etc.)

`tableStyleId` uses all-zero GUID (`{00000000-...}`) to disable PowerPoint's theme-default table style and preserve explicitly set cell colors.

### Chart Element Architecture

Charts use a two-file model:
1. **Slide XML** — `<p:graphicFrame>` with `<c:chart r:id="rIdN"/>` referencing an external file
2. **Chart file** — `ppt/charts/chartN.xml` (`<c:chartSpace>` root) with inline literal data

Data is fully self-contained — no embedded Excel workbook required. The relationship chain is:
```
slide1.xml → (rIdN) → ppt/charts/chart1.xml
```
Content type: `application/vnd.openxmlformats-officedocument.drawingml.chart+xml`

**`write_content_types` placement:** Must be called **after** `_write_slides()` so that `asset_manager.chart_counter` reflects the actual number of charts registered during slide building.

**`<c:ser>` element ordering (Fixed in v0.3.1):** OOXML CT_BarSer / CT_LineSer schema enforces this sequence:
```
idx → order → tx → spPr → [invertIfNegative] → cat → val
```
Placing `<c:spPr>` (series color) after `<c:cat>`/`<c:val>` causes PowerPoint to show a repair error.

**Axis definitions required (Fixed in v0.3.1):** `<c:barChart>` and `<c:lineChart>` must include:
- `<c:axId>` references inside the chart element pointing to defined axes
- `<c:catAx>` and `<c:valAx>` blocks inside `<c:plotArea>` (sibling of the chart element)

Without axes, PowerPoint cannot associate data with the coordinate system and renders the chart blank. Fixed axis IDs `64272128` (category) and `64274560` (value) are used — these are arbitrary stable integers, valid to reuse across charts.

Pie charts (`<c:pieChart>`) do not use axes.

**Series name format:** Use `<c:tx><c:v>Name</c:v></c:tx>` (literal value form) rather than `<c:strRef>` with an empty `<c:f/>` formula, which is unnecessarily fragile.

### Animation Complexity

Animations are **grouped by trigger** into `<p:seq>` (sequence) nodes:
1. Sort animations by `order`
2. Group by trigger: `on_click` starts new group, `with_previous`/`after_previous` join current group
3. Build nested `<p:cTn>` (timing nodes) with unique IDs
4. Each animation maps to a preset (appear→ID:1, fade→ID:10, fly_in→ID:2, etc.)

**Trigger mechanism:** Click groups use `delay="indefinite"` on their group-level `<p:cTn>` so PowerPoint waits for user click; auto-play groups (`with_previous`/`after_previous`) use `delay="0"`.

**`after_previous` timing:** Uses `nodeType="afterEffect"` + `delay="{delay_ms}"` on the animation-level `<p:cTn>`. MS Office interprets `delay` as the delay after the previous sibling animation ends (relative to previous end, NOT group start). Do NOT use `evt="onEnd"` + `<p:tn>` for intra-group sequencing — this breaks MS Office because `<p:par>` semantics conflict with sibling event references.

**Entrance animation initial hide:** Three pieces work together to make entrance-animated elements start hidden:
1. `<p:bldLst>` at end of `<p:timing>` — declares shapes that participate in build sequence (initially hidden); includes `animBg="1"` for WPS compatibility
2. `grpId="0"` on the animation's `<p:cTn>` — links animation to `<p:bldLst>` entry
3. `<p:set>` visibility="visible" inside `<p:childTnLst>` — makes shape visible when animation fires

Without all three, PowerPoint shows elements immediately instead of hiding them until animation trigger.

**`presetSubtype` always required:** Always output `presetSubtype="N"` on animation `<p:cTn>`, even when `N=0`. Omitting it causes inconsistent behavior in some renderers.

**`fill="hold"` on behavior nodes:** All `<p:cTn>` inside `<p:cBhvr>` (behavior timing nodes for animEffect, anim, animScale) must include `fill="hold"` so the animation state persists after completion.

**`fly_in` coordinate variables:**
- Vertical (top/bottom): axis=`ppt_y`, size=`#ppt_h`, end=`#ppt_y`
- Horizontal (left/right): axis=`ppt_x`, size=`#ppt_w`, end=`#ppt_x`
- Both: from_val = `"1+{size}/2"` (bottom/right) or `"-1-{size}/2"` (top/left)

### Transition Timing Bug (Fixed in v0.2.0)

**Issue:** Early code set `spd="600"` (numeric milliseconds), but OOXML requires `spd` to be enum ("slow"/"med"/"fast").

**Fix:** Map duration_ms → spd enum, also output `dur` (milliseconds) for precise timing:
```xml
<p:transition spd="med" dur="600">  <!-- correct -->
```

**Mapping rule:** ≤300ms → "fast", ≤700ms → "med", >700ms → "slow"

### Asset Loading

`AssetManager` tracks two categories of output resources:
- **Media** (`media_entries`) — image/PNG bytes written to `ppt/media/`; counter: `media_counter`
- **Charts** (`chart_entries`) — chart XML strings written to `ppt/charts/`; counter: `chart_counter`

SVG → PNG conversion via cairosvg (optional dependency). Unsupported image formats auto-convert to PNG.

---

## Where to Add New Features

### Adding a New Animation Type

1. Add entry to `ANIM_PRESETS` in `xml_builders/animations.py`
2. Add direction → presetSubtype mapping if needed (e.g., `FLY_IN_SUBTYPES`)
3. Implement behavior XML generation in `_build_anim_behavior_xml()`
4. Update `llm_prompt.md` table in section "8.3 type（动画类型）"
5. Add test case to `tests/test_exporter.py`

### Adding a New Transition Type

1. Implement in `xml_builders/transitions.py:build_transition_xml()`
2. Add to OOXML elem generation (if not already handled by dir_map)
3. Update `llm_prompt.md` section "九、页面时间线（timeline）"
4. Test with `test_new.json` example

### Adding a New Element Type

1. Create `xml_builders/<type>.py` with a `build_<type>_xml(ctx, elem, shape_id, ...)` function
2. Add dispatch branch in `ooxml/slides.py:build_single_slide_xml()`:
   - Register `element_shape_map[elem_id] = shape_id`
   - Collect any rel entries and increment `next_rel_id`
   - Increment `shape_id` (or use the returned value for recursive builders like groups)
3. If the element produces external files (like charts), add tracking to `AssetManager` and a `_write_<type>` method to `exporter.py`
4. Register content type in `ooxml/package.py:write_content_types()` if needed
5. Update `llm_prompt.md` section "七、元素（elements）"
6. Add test to `tests/test_exporter.py`

### Adding Element Rotation / Opacity

Already implemented via `BaseElement.rotation` (degrees → rot×60000) and `BaseElement.opacity` (0.0–1.0 → alpha×100000 or alphaModFix).

To extend to new element types, apply the pattern in `xml_builders/shapes.py:_build_xfrm_xml()`.

---

## Testing Strategy

- **Unit tests** (`test_utils.py`): Color parsing, EMU conversion, canvas sizing
- **Integration tests** (`test_exporter.py`): Full JSON→PPTX pipeline; newer tests also inspect ZIP contents with `zipfile.ZipFile` to verify XML structure
- **Manual verification**: Open generated PPTX in PowerPoint, check visual output and animation playback

**Test fixture:** `test_new.json` — a 13-slide presentation exercising gradient, rotation, opacity, transition, animations, group elements, table elements, and chart elements.

**JSON spec:** `llm_prompt.md` (v3.1) — the authoritative schema definition for LLM-generated JSON input. Keep this in sync with any feature additions.

---

## File Structure (Key Files Only)

```
src/pppt/
  exporter.py               # Main JsonToPptxExporter class, orchestrates phases
  context.py                # CompileContext dataclass
  assets.py                 # AssetManager: tracks media (images) + charts
  xml_builders/
    common.py               # fill/stroke/gradient XML helpers
    text.py                 # paragraph/run XML (shared across element types)
    shapes.py               # text box + shape elements
    pictures.py             # image/SVG elements
    groups.py               # group element (<p:grpSp>), recursive child dispatch
    tables.py               # table element (<p:graphicFrame>/<a:tbl>)
    charts.py               # chart slide frame + chart file XML
    backgrounds.py          # slide background (color/gradient)
    transitions.py          # slide transitions
    animations.py           # animation timing XML
  ooxml/
    slides.py               # per-slide XML assembly; dispatches all 7 element types
    package.py              # content types, root rels, ZIP packaging
    presentation.py         # presentation.xml, theme, slide master/layout, doc props
demo.py                     # Thin CLI wrapper
llm_prompt.md               # Complete JSON schema for LLM consumption (v3)
tests/
  test_exporter.py          # Integration tests (15 tests)
  test_utils.py             # Unit tests for utility functions
```

---

## Development Workflow

### For Bug Fixes

1. Write failing test in `tests/test_exporter.py`
2. Fix code, verify test passes
3. Run full test suite: `pytest tests/ -v`
4. Manual check: `pppt.cli test_new.json -o bug_fix_test.pptx` + open in PowerPoint

### For New Features

1. Update `llm_prompt.md` with JSON schema changes
2. Implement in appropriate xml_builders module
3. Add test (at minimum: JSON with feature → PPTX generation succeeds; for structural features, also verify ZIP contents)
4. Regenerate `test_new.json` to demonstrate feature
5. Run full test suite

### For OOXML Structure Changes

**Critical:** Validate against Microsoft's ECMA-376 spec. PowerPoint will show "repair" dialog if:
- Invalid XML nesting or element ordering (e.g., `<p:transition>` must be a sibling of `<p:cSld>`, not a child; `<a:tcPr>` border lines must precede fill; `<c:spPr>` must precede `<c:cat>`/`<c:val>` in chart series)
- Enum attribute with numeric value (e.g., `spd="600"` instead of `spd="med"`)
- Missing required child elements or malformed timing node IDs
- Charts missing `<c:catAx>`/`<c:valAx>` axis definitions (renders blank with repair dialog)

Test by opening generated PPTX in PowerPoint — if no repair dialog appears, structure is valid.

---

## Dependencies

- **Pillow** ≥9.0 — Image manipulation
- **cairosvg** ≥2.5 (optional) — SVG→PNG conversion
- **pytest** ≥7.0 (dev) — Testing

Install dev:
```bash
.venv/Scripts/pip.exe install ".[dev]"
```

---

## Known Limitations

1. **Animations** — Only 7 presets implemented; complex path animations not supported
2. **Group opacity** — `<p:grpSp>` has no direct opacity attribute; set opacity on individual children instead
3. **Pie charts** — Only first series is rendered (OOXML pie chart limitation)
4. **Master Slides** — Single master/layout hardcoded
5. **Custom Fonts** — Uses system fonts; embedded fonts not supported
6. **SVG** — Requires optional `cairosvg` dependency; converted to PNG for embedding

---
