from pathlib import Path

from p2s_core.models import (
    ClaimExtractionResult,
    NarrativeArcItem,
    NarrativePlan,
    PresentationReviewBundle,
    SceneRewritePatch,
    SceneRewriteResult,
    ScenesBundle,
)
from p2s_core.services import persistence
from p2s_core.services.llm_quality_rewrite import (
    RewriteGuardrailError,
    apply_rewrite_result,
    run_llm_quality_rewrite_stage,
)
from p2s_core.services.persona_style import load_presentation_profile
from p2s_core.services.presentation_planning import build_presentation_plan, build_scenes_bundle
from tests.test_mvp2a_fixtures import make_claim, make_state, reset_runs


ROOT = Path(__file__).resolve().parents[1]


class FakeLLM:
    model = "fake-rewrite"

    def __init__(self, result):
        self.result = result

    async def complete(self, *args, **kwargs):
        return self.result


def make_rewrite_project(monkeypatch, name="llm_quality_rewrite"):
    runs_dir = reset_runs(ROOT, name)
    monkeypatch.setattr(persistence, "RUNS_DIR", runs_dir)
    project_id = name
    project_dir = runs_dir / project_id
    project_dir.mkdir(parents=True)
    state = make_state(project_id)
    state.stages["extraction"].status = "done"
    state.stages["claim_extraction"].status = "done"
    state.stages["narrative_planning"].status = "done"
    state.stages["presentation_planning"].status = "done"
    claims = [
        make_claim("claim_001", "The paper addresses noisy labels.", "problem", 5),
        make_claim("claim_002", "The method compares two encoders.", "method", 4),
    ]
    claim_result = ClaimExtractionResult(
        project_id=project_id,
        claims=claims,
        source_chunk_ids=["chunk_001"],
        created_at="2026-05-08T00:00:00Z",
    )
    narrative = NarrativePlan(
        project_id=project_id,
        target_duration_sec=60,
        language="zh-TW",
        audience="general_science",
        selected_claim_ids=["claim_001", "claim_002"],
        narrative_arc=[
            NarrativeArcItem(purpose="hook", claim_ids=["claim_001"], intent="hook"),
            NarrativeArcItem(purpose="method", claim_ids=["claim_002"], intent="method"),
        ],
        rationale="test",
        created_at="2026-05-08T00:00:00Z",
    )
    profile = load_presentation_profile()
    scenes = build_scenes_bundle(state, claims, narrative, profile)
    plan = build_presentation_plan(project_id, scenes.scenes, profile)

    (project_dir / "claims.json").write_text(claim_result.model_dump_json(indent=2), encoding="utf-8")
    (project_dir / "narrative_plan.json").write_text(narrative.model_dump_json(indent=2), encoding="utf-8")
    (project_dir / "scenes.json").write_text(scenes.model_dump_json(indent=2), encoding="utf-8")
    (project_dir / "presentation_plan.json").write_text(plan.model_dump_json(indent=2), encoding="utf-8")
    persistence.save_state(state)
    return state, project_dir, scenes


def test_apply_rewrite_preserves_immutable_fields():
    state = make_state()
    claims = [make_claim("claim_001", "The paper addresses noisy labels.", "problem", 5)]
    narrative = NarrativePlan(
        project_id=state.project_id,
        target_duration_sec=60,
        language="zh-TW",
        audience="general_science",
        selected_claim_ids=["claim_001"],
        narrative_arc=[NarrativeArcItem(purpose="hook", claim_ids=["claim_001"], intent="hook")],
        rationale="test",
        created_at="2026-05-08T00:00:00Z",
    )
    scenes = build_scenes_bundle(state, claims, narrative, load_presentation_profile()).scenes
    result = SceneRewriteResult(
        project_id=state.project_id,
        patches=[
            SceneRewritePatch(
                scene_id=scenes[0].scene_id,
                voice_text="這篇研究關注 noisy labels。",
                subtitle_text="Noisy labels",
                asset_intent=None,
                notes_for_render="Keep presenter centered.",
            )
        ],
    )

    rewritten = apply_rewrite_result(scenes, result)

    assert rewritten[0].voice_text == "這篇研究關注 noisy labels。"
    assert rewritten[0].claim_ids == scenes[0].claim_ids
    assert rewritten[0].presenter_mode == scenes[0].presenter_mode


def test_apply_rewrite_rejects_unknown_or_missing_scene_ids():
    state = make_state()
    claims = [make_claim("claim_001", "The paper addresses noisy labels.", "problem", 5)]
    narrative = NarrativePlan(
        project_id=state.project_id,
        target_duration_sec=60,
        language="zh-TW",
        audience="general_science",
        selected_claim_ids=["claim_001"],
        narrative_arc=[NarrativeArcItem(purpose="hook", claim_ids=["claim_001"], intent="hook")],
        rationale="test",
        created_at="2026-05-08T00:00:00Z",
    )
    scenes = build_scenes_bundle(state, claims, narrative, load_presentation_profile()).scenes
    result = SceneRewriteResult(
        project_id=state.project_id,
        patches=[
            SceneRewritePatch(scene_id="scene_missing", voice_text="Bad.", subtitle_text="Bad.")
        ],
    )

    try:
        apply_rewrite_result(scenes, result)
    except RewriteGuardrailError as exc:
        assert "scene_id set" in str(exc)
    else:
        raise AssertionError("Expected RewriteGuardrailError")


def test_llm_quality_rewrite_pass_promotes_rewritten_scenes(monkeypatch):
    state, project_dir, scenes = make_rewrite_project(monkeypatch, "llm_quality_rewrite_pass")
    result = SceneRewriteResult(
        project_id=state.project_id,
        patches=[
            SceneRewritePatch(
                scene_id=scene.scene_id,
                voice_text=f"改寫：{scene.voice_text}",
                subtitle_text=f"改寫{index}",
                asset_intent=scene.asset_intent,
                notes_for_render=scene.notes_for_render,
            )
            for index, scene in enumerate(scenes.scenes, start=1)
        ],
        rewrite_model="fake-rewrite",
    )

    updated = run_llm_quality_rewrite_stage(state, llm=FakeLLM(result))

    assert (project_dir / "scenes_rewritten.json").exists()
    assert (project_dir / "reviews" / "llm_quality_rewrite_review_rev001.json").exists()
    assert updated.stages["llm_quality_rewrite"].status == "done"
    assert updated.active_scene_source == "scenes_rewritten.json"


def test_llm_quality_rewrite_unsupported_claim_does_not_promote(monkeypatch):
    state, project_dir, scenes = make_rewrite_project(monkeypatch, "llm_quality_rewrite_bad_claim")
    result = SceneRewriteResult(
        project_id=state.project_id,
        patches=[
            SceneRewritePatch(
                scene_id=scene.scene_id,
                voice_text="這完全解決了所有問題。",
                subtitle_text="完全解決",
                asset_intent=scene.asset_intent,
                notes_for_render=scene.notes_for_render,
            )
            for scene in scenes.scenes
        ],
    )

    updated = run_llm_quality_rewrite_stage(state, llm=FakeLLM(result))
    review = PresentationReviewBundle.model_validate_json(
        (project_dir / "reviews" / "llm_quality_rewrite_review_rev001.json").read_text(encoding="utf-8")
    )

    assert updated.stages["llm_quality_rewrite"].status == "needs_review"
    assert updated.active_scene_source == "scenes.json"
    assert review.gate_decision.status == "human_check"


def test_llm_quality_rewrite_subtitle_too_long_does_not_promote(monkeypatch):
    state, _project_dir, scenes = make_rewrite_project(monkeypatch, "llm_quality_rewrite_long_subtitle")
    result = SceneRewriteResult(
        project_id=state.project_id,
        patches=[
            SceneRewritePatch(
                scene_id=scene.scene_id,
                voice_text=scene.voice_text,
                subtitle_text="這是一個非常非常非常非常非常非常非常非常超長的字幕",
                asset_intent=scene.asset_intent,
                notes_for_render=scene.notes_for_render,
            )
            for scene in scenes.scenes
        ],
    )

    updated = run_llm_quality_rewrite_stage(state, llm=FakeLLM(result))

    assert updated.stages["llm_quality_rewrite"].status == "needs_review"
    assert updated.active_scene_source == "scenes.json"


def test_llm_quality_rewrite_missing_key_fails_without_promote(monkeypatch):
    state, _project_dir, _scenes = make_rewrite_project(monkeypatch, "llm_quality_rewrite_missing_key")
    import p2s_core.services.llm_quality_rewrite as rewrite_module

    monkeypatch.setattr(
        rewrite_module,
        "load_config",
        lambda path="config.yaml": {"llm": {"provider": "openai", "api_key": ""}},
    )

    try:
        run_llm_quality_rewrite_stage(state)
    except ValueError as exc:
        assert "OPENAI_API_KEY" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
    assert state.active_scene_source == "scenes.json"
