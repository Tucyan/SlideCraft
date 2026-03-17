---
name: "agent-ppt"
description: "Creates PowerPoint files from structured JSON input. Invoke when user asks to generate PPTX slides, convert JSON to presentation, or create slides programmatically."
---

# Agent PPT

This skill provides a JSON to PowerPoint (PPTX) conversion tool optimized for AI agents.

## Usage

The skill uses `JsonToPptxExporter` to convert structured JSON into valid PPTX files.

### CLI Usage

```bash
python -m pppt.cli input.json -o output.pptx
```

### Programmatic Usage

```python
from pppt import JsonToPptxExporter

exporter = JsonToPptxExporter(doc, output_path)
exporter.run()
```

### JSON Schema

The input JSON must follow the schema defined in `llm_prompt.md`. Key elements include:
- **Slides**: Array of slide objects with background, elements, transitions, animations
- **Elements**: text, shape, image, svg, group, table, chart
- **Properties**: position (x, y, w, h), rotation, opacity, colors, fonts, etc.

## Supported Features

- Text, shapes, images, SVG
- Groups and tables
- Charts (bar, line, pie)
- Animations (appear, fade, fly in, etc.)
- Transitions (fade, push, wipe)
- Gradients and opacity
- Rotation transforms

## Testing

Run tests with:
```bash
PYTHONPATH=src python -m pytest tests/ -v
```
