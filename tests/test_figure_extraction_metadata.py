import base64
from pathlib import Path

import fitz
import pytest

from p2s_core.services.figure_extraction import extract_figure_and_table_metadata, validate_figure_paths


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


def make_pdf_with_image(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Figure 1. Teacher model transmits traits through numbers.")
    page.insert_image(fitz.Rect(72, 100, 120, 148), stream=PNG_1X1)
    doc.save(path)
    doc.close()


def test_extracts_figure_metadata_and_image_path_inside_run_dir(tmp_path: Path):
    pdf = tmp_path / "paper.pdf"
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    make_pdf_with_image(pdf)

    figures, tables = extract_figure_and_table_metadata(pdf, run_dir)

    assert tables == []
    assert figures[0].figure_id == "fig_001"
    assert figures[0].caption
    assert figures[0].image_path
    assert (run_dir / figures[0].image_path).exists()
    validate_figure_paths(run_dir, [figures[0].model_dump()])


def test_validate_duplicate_figure_id_fails(tmp_path: Path):
    with pytest.raises(ValueError):
        validate_figure_paths(
            tmp_path,
            [
                {"figure_id": "fig_001", "image_path": None},
                {"figure_id": "fig_001", "image_path": None},
            ],
        )


def test_validate_image_path_outside_run_dir_fails(tmp_path: Path):
    with pytest.raises(ValueError):
        validate_figure_paths(tmp_path, [{"figure_id": "fig_001", "image_path": "../outside.png"}])
