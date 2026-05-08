from pathlib import Path

from p2s_core.models import (
    ClaimExtractionResult,
    EvidenceSpan,
    PaperClaim,
    ProjectSource,
    ProjectState,
    default_stages,
)
from p2s_core.services import persistence
from p2s_core.services.claim_extraction import run_claim_extraction_stage


ROOT = Path(__file__).resolve().parents[1]
TEST_RUNS_DIR = ROOT / ".test_runs" / "claim_extraction"


class FakeLLM:
    model = "fake-llm"

    def __init__(self, result):
        self.result = result

    async def complete(self, *args, **kwargs):
        return self.result


def reset_test_runs() -> Path:
    import shutil

    if TEST_RUNS_DIR.exists():
        shutil.rmtree(TEST_RUNS_DIR)
    TEST_RUNS_DIR.mkdir(parents=True)
    return TEST_RUNS_DIR / "runs"


def make_state(project_id: str) -> ProjectState:
    return ProjectState(
        project_id=project_id,
        created_at="2026-05-06T00:00:00Z",
        source=ProjectSource(pdf_path=f"runs/{project_id}/source.pdf"),
        persona={"persona_id": "seina", "version": "0.1.0"},
        style={"style_id": "rigorous_science_short", "version": "0.1.0"},
        stages=default_stages(),
    )


def test_run_claim_extraction_stage_writes_claims_and_review(monkeypatch):
    runs_dir = reset_test_runs()
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    project_id = "2026-05-06_claim_fake"
    project_dir = runs_dir / project_id
    project_dir.mkdir(parents=True)
    extracted_text = "Results\n\nThe proposed method improves accuracy by 5 percent on the benchmark dataset."
    extracted_path = project_dir / "extracted_text.md"
    extracted_path.write_text(extracted_text, encoding="utf-8")

    state = make_state(project_id)
    state.extraction.text_md = str(extracted_path)
    state.stages["extraction"].status = "done"
    persistence.save_state(state)

    llm_result = ClaimExtractionResult(
        project_id=project_id,
        claims=[
            PaperClaim(
                claim_id="claim_001",
                claim_text="The proposed method improves accuracy by 5 percent.",
                claim_type="result",
                source_section="result",
                evidence_spans=[
                    EvidenceSpan(
                        section="Results",
                        text="The proposed method improves accuracy by 5 percent on the benchmark dataset.",
                    )
                ],
                certainty="explicit",
                importance=5,
            )
        ],
        source_chunk_ids=["chunk_001"],
        extraction_model="fake-llm",
        created_at="2026-05-06T00:00:00Z",
        quality_report={"invalid_candidates": []},
    )

    updated = run_claim_extraction_stage(state, llm=FakeLLM(llm_result))

    claims_path = project_dir / "claims.json"
    review_path = project_dir / "reviews" / "claim_review_rev001.json"
    assert claims_path.exists()
    assert review_path.exists()
    assert updated.claims[0].claim_id == "claim_001"
    assert updated.reviews
    assert updated.stages["claim_extraction"].status == "done"
    assert str(claims_path) in updated.stages["claim_extraction"].output_paths
    assert str(review_path) in updated.stages["claim_extraction"].output_paths
