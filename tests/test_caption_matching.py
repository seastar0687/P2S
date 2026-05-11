from p2s_core.services.figure_extraction import extract_captions_from_text


def test_caption_prefixes():
    captions = extract_captions_from_text(
        "Fig. 1: Result overview\nFigure 2. Architecture\nTable 1: Scores\n圖 3：範例\n表 4：資料"
    )

    assert [item["kind"] for item in captions] == ["figure", "figure", "table", "figure", "table"]


def test_no_caption_case():
    assert extract_captions_from_text("This is ordinary body text.") == []
