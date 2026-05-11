from p2s_core.services.text_normalization import normalize_text


def test_normalize_hyphenated_line_breaks():
    assert "transformer" in normalize_text("trans-\nformer")


def test_normalize_repeated_whitespace_and_ligatures():
    text = normalize_text("A\u00a0  ﬁgure   with   spaces")

    assert text == "A figure with spaces"


def test_normalize_line_break_artifacts_preserves_paragraphs():
    text = normalize_text("This line\ncontinues.\n\nNew paragraph.")

    assert "This line continues." in text
    assert "\n\nNew paragraph." in text
