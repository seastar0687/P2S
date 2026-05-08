from __future__ import annotations

from pathlib import Path

from p2s_core.models import ProjectState
from p2s_core.services import persistence


def extract_text(pdf_path: str | Path) -> str:
    """Extract plain text from a PDF with PyMuPDF."""

    import fitz

    with fitz.open(str(pdf_path)) as doc:
        return "\n\n".join(page.get_text() for page in doc)


def run_extraction_stage(state: ProjectState) -> ProjectState:
    text = extract_text(state.source.pdf_path)
    output_path = persistence.project_dir(state.project_id) / "extracted_text.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")

    state.extraction.text_md = str(output_path)
    state.stages["extraction"].status = "done"
    state.stages["extraction"].output_paths = [str(output_path)]
    return state
