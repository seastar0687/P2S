from pathlib import Path

from p2s_core.models import ClaimExtractionResult
from p2s_core.services import persistence
from p2s_core.services.narrative_planning import build_narrative_plan, run_narrative_planning_stage
from tests.test_mvp2a_fixtures import make_claim, make_state, reset_runs


ROOT = Path(__file__).resolve().parents[1]


def test_narrative_plan_uses_only_valid_accepted_claim_ids():
    state = make_state()
    claims = [
        make_claim("claim_001", "The paper addresses noisy labels.", "problem", 5),
        make_claim("claim_002", "The method compares two encoders.", "method", 4),
        make_claim("claim_003", "Unsupported claim.", "result", 5, ["unsupported"]),
    ]

    plan = build_narrative_plan(state, claims)

    assert "claim_001" in plan.selected_claim_ids
    assert "claim_002" in plan.selected_claim_ids
    assert "claim_003" not in plan.selected_claim_ids
    valid_ids = {claim.claim_id for claim in claims if "unsupported" not in claim.risk_flags}
    for item in plan.narrative_arc:
        assert set(item.claim_ids).issubset(valid_ids)


def test_narrative_plan_requires_accepted_claims():
    state = make_state()

    try:
        build_narrative_plan(state, [make_claim("claim_001", "Bad.", risk_flags=["missing_evidence"])])
    except ValueError as exc:
        assert "no accepted grounded claims" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_narrative_plan_includes_high_importance_limitation():
    state = make_state()
    claims = [
        make_claim("claim_001", "The paper proposes a new method.", "method", 5),
        make_claim("claim_002", "The method improves one benchmark.", "result", 5),
        make_claim("claim_003", "The study is limited to synthetic data.", "limitation", 4),
    ]

    plan = build_narrative_plan(state, claims)

    assert "claim_003" in plan.selected_claim_ids
    assert any(item.purpose == "limitation" and "claim_003" in item.claim_ids for item in plan.narrative_arc)


def test_run_narrative_planning_stage_reads_claims_json_and_writes_output(monkeypatch):
    runs_dir = reset_runs(ROOT, "narrative_planning")
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    project_id = "mvp2a_narrative"
    project_dir = runs_dir / project_id
    project_dir.mkdir(parents=True)
    state = make_state(project_id)
    state.stages["extraction"].status = "done"
    state.stages["claim_extraction"].status = "done"
    result = ClaimExtractionResult(
        project_id=project_id,
        claims=[make_claim("claim_001", "The paper proposes a new method.", "method", 5)],
        source_chunk_ids=["chunk_001"],
        created_at="2026-05-08T00:00:00Z",
    )
    (project_dir / "claims.json").write_text(result.model_dump_json(indent=2), encoding="utf-8")

    updated = run_narrative_planning_stage(state)

    assert (project_dir / "narrative_plan.json").exists()
    assert updated.stages["narrative_planning"].status == "done"
    assert updated.stages["narrative_planning"].output_paths == ["narrative_plan.json"]
    assert updated.narrative_plan["selected_claim_ids"] == ["claim_001"]
