from pathlib import Path

from p2s_core.models import EvidenceSpan, PaperClaim, ProjectSource, ProjectState, default_stages


def make_claim(
    claim_id: str,
    claim_text: str,
    claim_type: str = "method",
    importance: int = 4,
    risk_flags: list[str] | None = None,
) -> PaperClaim:
    return PaperClaim(
        claim_id=claim_id,
        claim_text=claim_text,
        claim_type=claim_type,
        source_section="Test",
        evidence_spans=[
            EvidenceSpan(section="Test", text=f"Evidence for {claim_text}")
        ],
        certainty="explicit",
        importance=importance,
        risk_flags=risk_flags or [],
    )


def make_state(project_id: str = "mvp2a_test") -> ProjectState:
    return ProjectState(
        project_id=project_id,
        created_at="2026-05-08T00:00:00Z",
        source=ProjectSource(pdf_path=f"runs/{project_id}/source.pdf"),
        persona={"persona_id": "seina", "version": "0.1.0"},
        style={
            "style_id": "rigorous_science_short",
            "version": "0.1.0",
            "sentence_rules": {"max_voice_chars_per_scene": 55},
            "subtitle_rules": {"max_subtitle_chars": 24},
            "forbidden_phrases_path": "forbidden_phrases.txt",
        },
        stages=default_stages(),
    )


def reset_runs(root: Path, name: str) -> Path:
    import shutil

    test_dir = root / ".test_runs" / name
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True)
    return test_dir / "runs"
