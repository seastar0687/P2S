from tests.test_mvp2c_thin_pipeline import make_scene
from p2s_core.services.subtitle_quality import check_subtitle_readability


def test_short_subtitle_passes():
    result = check_subtitle_readability(make_scene())

    assert result.pass_gate is True
    assert result.estimated_lines == 1


def test_empty_and_long_subtitles_warn_or_fail():
    empty = make_scene()
    empty.subtitle_text = ""
    long = make_scene()
    long.subtitle_text = "This subtitle is deliberately far too long for a compact short-form safe area."

    assert check_subtitle_readability(empty).warnings
    result = check_subtitle_readability(long)
    assert result.too_long is True
    assert result.pass_gate is False
