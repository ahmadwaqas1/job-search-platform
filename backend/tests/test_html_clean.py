from app.utils.html_clean import strip_html


def test_strip_html_removes_tags():
    assert strip_html("<p>Hello <b>world</b></p>") == "Hello world"


def test_strip_html_unescapes_entities():
    assert "&" in strip_html("Sales &amp; Marketing")


def test_strip_html_collapses_blank_lines():
    raw = "<p>One</p><p></p><p></p><p>Two</p>"
    result = strip_html(raw)
    assert "\n\n\n" not in result


def test_strip_html_empty_input():
    assert strip_html("") == ""
    assert strip_html(None) == ""  # type: ignore[arg-type]
