from typing import get_args

from p2s_core.models import (
    ClaimExtractionResult,
    ClaimReviewBundle,
    EvidenceSpan,
    PaperClaim,
    PaperChunk,
    PaperSection,
    PresentationPlan,
    PresentationProfile,
    PresentationScene,
    PersonaProfile,
    ProjectSource,
    ProjectState,
    GateDecision,
    NarrativeArcItem,
    NarrativePlan,
    ReviewResult,
    Scene,
    SceneDraft,
    SceneRewritePatch,
    SceneRewriteResult,
    ScenesBundle,
    PresentationReviewBundle,
    StageState,
    StyleProfile,
    default_stages,
)


def roundtrip(model):
    payload = model.model_dump_json()
    return type(model).model_validate_json(payload)


def test_evidence_span_roundtrip():
    span = EvidenceSpan(
        section="3.2 Experimental Setup",
        text="We evaluate the method on three benchmark datasets.",
        page=4,
        confidence="direct",
    )

    assert roundtrip(span) == span


def test_paper_claim_roundtrip():
    claim = PaperClaim(
        claim_id="claim_001",
        claim_text="The proposed method improves benchmark accuracy.",
        claim_type="result",
        source_section="4 Results",
        evidence_spans=[
            EvidenceSpan(
                section="4 Results",
                text="Our method achieves the highest average score.",
                page=7,
            )
        ],
        certainty="explicit",
        importance=5,
    )

    assert roundtrip(claim) == claim


def test_paper_section_and_chunk_roundtrip():
    section = PaperSection(
        section_id="section_001",
        title="Abstract",
        section_type="abstract",
        text="This paper introduces a method.",
        start_char=0,
        end_char=32,
    )
    chunk = PaperChunk(
        chunk_id="chunk_001",
        section_id="section_001",
        section_type="abstract",
        text=section.text,
        char_start=0,
        char_end=32,
        token_estimate=8,
    )

    assert roundtrip(section) == section
    assert roundtrip(chunk) == chunk


def test_claim_extraction_result_roundtrip():
    result = ClaimExtractionResult(
        project_id="demo",
        claims=[
            PaperClaim(
                claim_id="claim_001",
                claim_text="The paper introduces a method.",
                claim_type="method",
                source_section="Abstract",
                evidence_spans=[
                    EvidenceSpan(section="Abstract", text="This paper introduces a method.")
                ],
                certainty="explicit",
                importance=4,
            )
        ],
        source_chunk_ids=["chunk_001"],
        extraction_model="fake",
        created_at="2026-05-06T00:00:00Z",
        quality_report={"invalid_candidates": []},
    )

    loaded = roundtrip(result)
    assert loaded == result
    assert loaded.source_chunk_ids == ["chunk_001"]


def test_claim_extraction_result_rejects_accepted_claim_without_evidence():
    try:
        ClaimExtractionResult(
            project_id="demo",
            claims=[
                PaperClaim(
                    claim_id="claim_001",
                    claim_text="A claim without evidence.",
                    claim_type="result",
                    source_section="Abstract",
                    evidence_spans=[],
                    certainty="explicit",
                    importance=3,
                )
            ],
            source_chunk_ids=["chunk_001"],
            created_at="2026-05-06T00:00:00Z",
        )
    except ValueError as exc:
        assert "accepted claims must have evidence_spans" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_claim_review_bundle_roundtrip():
    review = ReviewResult(
        review_id="review_001",
        target_type="claim",
        target_id="claim_001",
        reviewer="ClaimEvidenceReviewer",
        score=1.0,
        pass_gate=True,
        created_at="2026-05-06T00:00:00Z",
    )
    bundle = ClaimReviewBundle(
        project_id="demo",
        reviews=[review],
        gate_decision=GateDecision(
            gate_name="claim_extraction_gate",
            target_type="artifact",
            target_id="claim_extraction",
            status="pass",
            contributing_reviews=["review_001"],
            created_at="2026-05-06T00:00:00Z",
        ),
        created_at="2026-05-06T00:00:00Z",
    )

    assert roundtrip(bundle) == bundle


def test_scene_roundtrip():
    scene = Scene(
        scene_id="scene_001",
        purpose="method",
        claim_ids=["claim_001"],
        voice_text="The core idea is to compare representations before prediction.",
        subtitle_text="Compare first, predict later.",
        presenter_mode="speaking_with_overlay",
        visual_focus="supporting_asset",
        asset_policy="required",
        asset_intent="A clean block diagram of the method.",
        asset_type_hint="diagram",
        visual_prompt="A clean block diagram of the method.",
        target_duration_sec=8.0,
    )

    assert roundtrip(scene) == scene


def test_persona_profile_roundtrip():
    persona = PersonaProfile(
        persona_id="seina",
        name="Seina",
        role="paper explainer",
        positioning="A calm science companion for short paper explainers.",
        personality_traits=["calm", "curious", "precise"],
        speaking_style_summary="Gentle, concise, and evidence-aware.",
        relationship_to_audience="Friendly guide",
        allowed_emotional_range=["neutral", "curious", "gentle"],
        prompt_profile_path="prompt_profile.md",
        speaking_rules_path="speaking_rules.md",
        example_paths=["examples/short_explainer_01.md"],
        version="0.1.0",
        created_at="2026-05-06T00:00:00Z",
        updated_at="2026-05-06T00:00:00Z",
    )

    loaded = roundtrip(persona)
    assert loaded == persona
    assert loaded.vrm is None
    assert loaded.visual_identity is None


def test_style_profile_roundtrip():
    style = StyleProfile(
        style_id="rigorous_science_short",
        name="Rigorous Science Short",
        summary="Short-form science explanation without unsupported hype.",
        target_platforms=["youtube_shorts", "reels", "tiktok"],
        target_audience="general_science",
        language="zh-TW",
        narrative_structure=["hook", "problem", "method", "result", "limitation", "takeaway"],
        pacing="moderate",
        humor_level=1,
        rigor_level=5,
        metaphor_level=2,
        allowed_rhetorical_devices=["controlled_question_hook", "simple_analogy"],
        forbidden_rhetorical_devices=["clickbait_exaggeration"],
        sentence_rules={"max_voice_chars_per_scene": 55},
        subtitle_rules={"max_subtitle_chars": 24},
        hook_rules={"must_be_supported_by_paper": True},
        transition_rules={"prefer_logical_links": True},
        limitation_rules={"must_include_uncertainty": True},
        prompt_guide_path="prompt_guide.md",
        example_paths=["examples/good_01.md", "examples/bad_overhyped.md"],
        forbidden_phrases_path="forbidden_phrases.txt",
        version="0.1.0",
    )

    assert roundtrip(style) == style


def test_project_state_roundtrip():
    state = ProjectState(
        project_id="2026-05-06_test",
        created_at="2026-05-06T00:00:00Z",
        source=ProjectSource(pdf_path="runs/2026-05-06_test/source.pdf"),
        persona={"persona_id": "seina", "version": "0.1.0"},
        style={"style_id": "rigorous_science_short", "version": "0.1.0"},
        claims=[
            PaperClaim(
                claim_id="claim_001",
                claim_text="A grounded claim.",
                claim_type="method",
                source_section="2 Method",
                evidence_spans=[EvidenceSpan(section="2 Method", text="The model uses two encoders.")],
                certainty="explicit",
                importance=4,
            )
        ],
        reviews=[
            ReviewResult(
                review_id="review_001",
                target_type="claim",
                target_id="claim_001",
                reviewer="PaperFidelityReviewer",
                score=0.9,
                pass_gate=True,
                created_at="2026-05-06T00:00:00Z",
            )
        ],
        stages=default_stages(),
    )

    loaded = roundtrip(state)

    assert loaded == state
    assert set(loaded.stages) == set(default_stages())
    assert all(isinstance(stage, StageState) for stage in loaded.stages.values())
    assert "presentation_planning" in loaded.stages
    assert "llm_quality_rewrite" in loaded.stages
    assert "asset_preparation" in loaded.stages
    assert loaded.active_scene_source == "scenes.json"
    assert "script_generation" not in loaded.stages
    assert "storyboard_planning" not in loaded.stages


def test_scene_presentation_fields_consistency():
    for field_name in ("presenter_mode", "visual_focus", "asset_policy", "asset_type_hint", "background_mode"):
        scene_fields = Scene.model_fields[field_name].annotation
        draft_fields = SceneDraft.model_fields[field_name].annotation

        assert get_args(scene_fields) == get_args(draft_fields)

    assert get_args(Scene.model_fields["presenter_mode"].annotation) == (
        "speaking_on_camera",
        "speaking_with_overlay",
        "silent_presence",
        "minimized",
        "off_screen",
    )
    assert Scene.model_fields["visual_type"].annotation == str | None
    assert SceneDraft.model_fields["visual_type"].annotation == str | None


def test_presentation_plan_roundtrip():
    profile = PresentationProfile(
        profile_id="presenter_first_default",
        name="Presenter First Default",
        description="3D presenter-led scenes with optional supporting assets.",
        presenter_priority="high",
        default_background_mode="static_clean",
    )
    plan = PresentationPlan(
        project_id="demo",
        profile_id=profile.profile_id,
        scenes=[
            PresentationScene(
                scene_id="scene_001",
                scene_type="presenter_with_overlay",
                presenter_mode="speaking_with_overlay",
                visual_focus="supporting_asset",
                asset_policy="required",
                asset_type_hint="diagram",
                background_mode="static_clean",
                estimated_asset_duration_sec=6.0,
            )
        ],
        presenter_visibility_ratio=1.0,
        asset_scene_ratio=1.0,
        fullscreen_asset_ratio=0.0,
        created_at="2026-05-08T00:00:00Z",
    )

    assert roundtrip(profile) == profile
    assert roundtrip(plan) == plan


def test_mvp2a_output_bundles_roundtrip():
    narrative_plan = NarrativePlan(
        project_id="demo",
        target_duration_sec=60,
        language="zh-TW",
        audience="general_science",
        selected_claim_ids=["claim_001"],
        narrative_arc=[
            NarrativeArcItem(
                purpose="hook",
                claim_ids=["claim_001"],
                intent="Use a grounded hook.",
            )
        ],
        omitted_claim_ids=[],
        rationale="test",
        created_at="2026-05-08T00:00:00Z",
    )
    scenes = ScenesBundle(
        project_id="demo",
        scenes=[
            SceneDraft(
                scene_id="scene_001",
                purpose="hook",
                claim_ids=["claim_001"],
                voice_text="A grounded claim.",
                subtitle_text="Grounded.",
                target_duration_sec=6.0,
            )
        ],
        created_at="2026-05-08T00:00:00Z",
    )
    review = ReviewResult(
        review_id="presentation_001",
        target_type="presentation",
        target_id="presentation_planning",
        reviewer="PresentationStructureReviewer",
        score=1.0,
        pass_gate=True,
        created_at="2026-05-08T00:00:00Z",
    )
    bundle = PresentationReviewBundle(
        project_id="demo",
        reviews=[review],
        gate_decision=GateDecision(
            gate_name="presentation_gate",
            target_type="presentation",
            target_id="presentation_planning",
            status="pass",
            summary="Presentation gate passed.",
            created_at="2026-05-08T00:00:00Z",
        ),
        created_at="2026-05-08T00:00:00Z",
    )

    assert roundtrip(narrative_plan) == narrative_plan
    assert roundtrip(scenes) == scenes
    assert roundtrip(bundle) == bundle


def test_scene_draft_rejects_invalid_presentation_literals():
    base = {
        "scene_id": "scene_001",
        "purpose": "hook",
        "claim_ids": ["claim_001"],
        "voice_text": "A grounded claim.",
        "subtitle_text": "Grounded.",
        "target_duration_sec": 6.0,
    }

    for field_name, bad_value in (
        ("presenter_mode", "standing_on_moon"),
        ("visual_focus", "laser_show"),
        ("asset_policy", "always"),
    ):
        try:
            SceneDraft(**base, **{field_name: bad_value})
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected invalid {field_name} to fail")


def test_scene_rewrite_result_roundtrip_and_forbids_extra_fields():
    result = SceneRewriteResult(
        project_id="demo",
        patches=[
            SceneRewritePatch(
                scene_id="scene_001",
                voice_text="Rewritten voice.",
                subtitle_text="Rewritten.",
                asset_intent="A clearer asset intent.",
                notes_for_render="Keep it simple.",
            )
        ],
        rewrite_model="fake",
    )

    assert roundtrip(result) == result

    try:
        SceneRewritePatch(
            scene_id="scene_001",
            voice_text="Bad.",
            subtitle_text="Bad.",
            claim_ids=["claim_001"],
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Expected extra immutable field to be rejected")
