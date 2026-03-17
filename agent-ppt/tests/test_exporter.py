import json
import os
import tempfile
import zipfile

from pppt.exporter import JsonToPptxExporter


MINIMAL_DOC = {
    "version": "2.0",
    "metadata": {
        "presentation_id": "test_001",
        "title": "Test Presentation",
        "author": "test",
        "language": "en-US"
    },
    "theme": {
        "name": "test",
        "slide_size": "16:9",
        "background_default": {
            "type": "color",
            "color": "#FFFFFF"
        },
        "font_scheme": {
            "heading_font": "Arial",
            "body_font": "Arial"
        },
        "color_scheme": {
            "primary": "#000000",
            "secondary": "#333333"
        }
    },
    "assets": [],
    "slides": [
        {
            "slide_id": "slide_01",
            "index": 1,
            "title": "Test Slide",
            "layout": "blank",
            "elements": [
                {
                    "id": "text_01",
                    "type": "text",
                    "bbox": {"x": 100, "y": 100, "w": 400, "h": 200},
                    "z_index": 1,
                    "rotation": 45,
                    "opacity": 0.8,
                    "text": {
                        "paragraphs": [
                            {
                                "runs": [
                                    {"text": "Hello World", "bold": True, "italic": True, "underline": True}
                                ]
                            }
                        ]
                    }
                },
                {
                    "id": "shape_01",
                    "type": "shape",
                    "bbox": {"x": 600, "y": 100, "w": 300, "h": 200},
                    "z_index": 2,
                    "shape": "round_rect",
                    "fill": {"type": "solid", "color": "#FF0000"},
                    "stroke": {"color": "#000000", "width": 2},
                    "text": {
                        "paragraphs": [
                            {
                                "runs": [
                                    {"text": "Shape Text", "italic": True, "underline": True}
                                ],
                                "bullet": {"type": "disc"}
                            }
                        ]
                    }
                }
            ],
            "timeline": {
                "transition": {
                    "type": "fade",
                    "duration_ms": 500
                }
            },
            "animations": [
                {
                    "anim_id": "anim_01",
                    "target_id": "text_01",
                    "trigger": "with_previous",
                    "type": "fade",
                    "duration_ms": 600,
                    "order": 1
                },
                {
                    "anim_id": "anim_02",
                    "target_id": "shape_01",
                    "trigger": "after_previous",
                    "type": "appear",
                    "duration_ms": 500,
                    "order": 2
                }
            ]
        }
    ]
}


def test_exporter_creates_pptx():
    with tempfile.TemporaryDirectory() as tmpdir:
        output = os.path.join(tmpdir, "test.pptx")
        exporter = JsonToPptxExporter(MINIMAL_DOC, output)
        exporter.build()
        assert os.path.exists(output)
        assert os.path.getsize(output) > 0


def test_exporter_4_3():
    doc = json.loads(json.dumps(MINIMAL_DOC))
    doc["theme"]["slide_size"] = "4:3"
    with tempfile.TemporaryDirectory() as tmpdir:
        output = os.path.join(tmpdir, "test_43.pptx")
        exporter = JsonToPptxExporter(doc, output)
        exporter.build()
        assert os.path.exists(output)


def test_exporter_gradient_background():
    doc = json.loads(json.dumps(MINIMAL_DOC))
    doc["slides"][0]["background"] = {
        "type": "gradient",
        "gradient": {
            "angle": 90,
            "stops": [
                {"offset": 0, "color": "#FF0000"},
                {"offset": 1, "color": "#0000FF"}
            ]
        }
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        output = os.path.join(tmpdir, "test_gradient.pptx")
        exporter = JsonToPptxExporter(doc, output)
        exporter.build()
        assert os.path.exists(output)


def test_exporter_language_en():
    doc = json.loads(json.dumps(MINIMAL_DOC))
    doc["metadata"]["language"] = "en-US"
    with tempfile.TemporaryDirectory() as tmpdir:
        output = os.path.join(tmpdir, "test_lang.pptx")
        exporter = JsonToPptxExporter(doc, output)
        assert exporter.language == "en-US"
        exporter.build()
        assert os.path.exists(output)


def _make_doc_with_slide(elements, animations=None):
    """Helper: create a minimal valid doc with given elements on slide 1."""
    doc = json.loads(json.dumps(MINIMAL_DOC))
    doc["slides"][0]["elements"] = elements
    doc["slides"][0]["animations"] = animations or []
    return doc


def test_exporter_group_element():
    elements = [
        {
            "id": "group_01",
            "type": "group",
            "bbox": {"x": 100, "y": 100, "w": 800, "h": 400},
            "z_index": 1,
            "children": [
                {
                    "id": "grp_text",
                    "type": "text",
                    "bbox": {"x": 0, "y": 0, "w": 400, "h": 200},
                    "z_index": 1,
                    "text": {"paragraphs": [{"runs": [{"text": "Group Child"}]}]},
                },
                {
                    "id": "grp_shape",
                    "type": "shape",
                    "bbox": {"x": 400, "y": 0, "w": 400, "h": 200},
                    "z_index": 2,
                    "shape": "rect",
                    "fill": {"type": "solid", "color": "#2563EB"},
                },
            ],
        }
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        output = os.path.join(tmpdir, "test_group.pptx")
        exporter = JsonToPptxExporter(_make_doc_with_slide(elements), output)
        exporter.build()
        assert os.path.exists(output)
        with zipfile.ZipFile(output) as zf:
            slide_xml = zf.read("ppt/slides/slide1.xml").decode("utf-8")
        assert "<p:grpSp>" in slide_xml
        assert "Group Child" in slide_xml


def test_exporter_group_animation():
    elements = [
        {
            "id": "group_02",
            "type": "group",
            "bbox": {"x": 100, "y": 100, "w": 600, "h": 300},
            "z_index": 1,
            "children": [
                {
                    "id": "grp_child_a",
                    "type": "shape",
                    "bbox": {"x": 0, "y": 0, "w": 200, "h": 200},
                    "z_index": 1,
                    "shape": "ellipse",
                    "fill": {"type": "solid", "color": "#FF0000"},
                }
            ],
        }
    ]
    animations = [
        {
            "anim_id": "ag1",
            "target_id": "group_02",
            "trigger": "with_previous",
            "type": "fade",
            "duration_ms": 500,
            "order": 1,
        }
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        output = os.path.join(tmpdir, "test_group_anim.pptx")
        exporter = JsonToPptxExporter(
            _make_doc_with_slide(elements, animations), output
        )
        exporter.build()
        assert os.path.exists(output)
        with zipfile.ZipFile(output) as zf:
            slide_xml = zf.read("ppt/slides/slide1.xml").decode("utf-8")
        assert "<p:timing>" in slide_xml


def test_exporter_table_element():
    elements = [
        {
            "id": "table_01",
            "type": "table",
            "bbox": {"x": 100, "y": 200, "w": 1200, "h": 400},
            "z_index": 1,
            "rows": 2,
            "cols": 3,
            "borders": {"color": "#CCCCCC", "width": 1},
            "cells": [
                {
                    "row": 0,
                    "col": 0,
                    "fill_color": "#2563EB",
                    "text": {
                        "paragraphs": [{"runs": [{"text": "Header", "bold": True}]}]
                    },
                    "text_style": {"align": "center", "vertical_align": "middle"},
                },
                {
                    "row": 1,
                    "col": 1,
                    "text": {
                        "paragraphs": [{"runs": [{"text": "Cell Text"}]}]
                    },
                },
            ],
        }
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        output = os.path.join(tmpdir, "test_table.pptx")
        exporter = JsonToPptxExporter(_make_doc_with_slide(elements), output)
        exporter.build()
        assert os.path.exists(output)
        with zipfile.ZipFile(output) as zf:
            slide_xml = zf.read("ppt/slides/slide1.xml").decode("utf-8")
        assert "<a:tbl>" in slide_xml
        assert "Header" in slide_xml
        assert "Cell Text" in slide_xml


def test_exporter_chart_element():
    elements = [
        {
            "id": "chart_01",
            "type": "chart",
            "bbox": {"x": 100, "y": 200, "w": 900, "h": 500},
            "z_index": 1,
            "chart_type": "bar",
            "title": "季度销售额",
            "categories": ["Q1", "Q2", "Q3", "Q4"],
            "series": [
                {"name": "产品A", "values": [100, 150, 180, 200], "color": "#2563EB"}
            ],
        }
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        output = os.path.join(tmpdir, "test_chart.pptx")
        exporter = JsonToPptxExporter(_make_doc_with_slide(elements), output)
        exporter.build()
        assert os.path.exists(output)
        with zipfile.ZipFile(output) as zf:
            names = zf.namelist()
            assert "ppt/charts/chart1.xml" in names

            rels_xml = zf.read("ppt/slides/_rels/slide1.xml.rels").decode("utf-8")
            assert "relationships/chart" in rels_xml

            ct_xml = zf.read("[Content_Types].xml").decode("utf-8")
            assert "drawingml.chart+xml" in ct_xml


def test_exporter_chart_types():
    def _chart_doc(chart_type):
        elements = [
            {
                "id": f"chart_{chart_type}",
                "type": "chart",
                "bbox": {"x": 100, "y": 100, "w": 800, "h": 500},
                "z_index": 1,
                "chart_type": chart_type,
                "categories": ["A", "B", "C"],
                "series": [{"name": "S1", "values": [10, 20, 30]}],
            }
        ]
        return _make_doc_with_slide(elements)

    expected = {
        "bar": "<c:barChart>",
        "line": "<c:lineChart>",
        "pie": "<c:pieChart>",
    }
    for chart_type, expected_tag in expected.items():
        with tempfile.TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, f"test_{chart_type}.pptx")
            exporter = JsonToPptxExporter(_chart_doc(chart_type), output)
            exporter.build()
            assert os.path.exists(output)
            with zipfile.ZipFile(output) as zf:
                chart_xml = zf.read("ppt/charts/chart1.xml").decode("utf-8")
            assert expected_tag in chart_xml, (
                f"Expected {expected_tag!r} in chart XML for type {chart_type!r}"
            )
