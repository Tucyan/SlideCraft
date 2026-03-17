from pppt.utils import hex_to_rgb, canvas_to_slide_emu, rect_px_to_emu


def test_hex_to_rgb_basic():
    assert hex_to_rgb("#FF0000") == "FF0000"
    assert hex_to_rgb("#abc") == "AABBCC"
    assert hex_to_rgb("") == "000000"
    assert hex_to_rgb(None) == "000000"


def test_hex_to_rgb_invalid():
    assert hex_to_rgb("xyz") == "000000"
    assert hex_to_rgb("#12345G") == "000000"


def test_canvas_to_slide_emu_16_9():
    w, h = canvas_to_slide_emu(1920, 1080)
    assert w == 12192000
    assert h == 6858000


def test_canvas_to_slide_emu_4_3():
    w, h = canvas_to_slide_emu(1440, 1080)
    assert w == 9144000
    assert h == 6858000


def test_canvas_to_slide_emu_custom():
    w, h = canvas_to_slide_emu(800, 600)
    assert w > 0
    assert h > 0


def test_rect_px_to_emu():
    rect = {"x": 0, "y": 0, "w": 1920, "h": 1080}
    x, y, cx, cy = rect_px_to_emu(rect, 1920, 1080, 12192000, 6858000)
    assert x == 0
    assert y == 0
    assert cx == 12192000
    assert cy == 6858000
