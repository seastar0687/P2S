# IMPLEMENTATION_PLAN_MVP2A.md

> Version: v0.1  
> Status: Sprint Contract  
> Depends on: `P2S_redesign_architecture_v8.1.md`, `IMPLEMENTATION_PLAN_MVP1_v2.md`  
> Target stage: `presentation_planning`  
> Core scope: `claims.json → narrative_plan.json → scenes.json → presentation_plan.json → reviews/presentation_review_rev001.json`

---

## 0. Purpose

MVP2A is the first step after MVP1 claim grounding. Its job is **not** to generate a final video, and not even to prepare concrete media assets. Its job is to convert grounded paper claims into a **claim-grounded presentation plan** that can later be performed by a 3D presenter, supported by sparse visual assets, and rendered over a low-interference background.

MVP2A answers one question:

> Given a valid `claims.json`, can P2S produce a short-form, claim-grounded, presentation-aware plan whose text, scene structure, presenter usage, asset density, and background strategy are inspectable and reviewable?

The output should be useful even before any TTS, image generation, VRM rendering, or video composition exists.

---

## 1. Scope Boundary

### 1.1 In Scope

MVP2A implements:

```text
claims.json
→ narrative_plan.json
→ scenes.json
→ presentation_plan.json
→ reviews/presentation_review_rev001.json
```

Required capabilities:

1. Load existing `claims.json` from an MVP1 project.
2. Load selected `persona`, `style`, and `presentation_profile`.
3. Generate a narrative plan from accepted grounded claims.
4. Generate `SceneDraft` records with claim links and presentation fields.
5. Generate a `PresentationPlan` summarizing presenter / asset / background strategy.
6. Run deterministic and/or minimal LLM reviewers for grounding, style rules, and presentation structure.
7. Save all outputs to `runs/{project_id}/`.
8. Update `project_state.json` stage status for `narrative_planning` and `presentation_planning`.
9. Add tests for schema, stage execution, fake LLM output, and reviewer gates.

### 1.2 Explicitly Out of Scope

MVP2A must not implement:

```text
✗ TTS generation
✗ Edge-TTS integration beyond existing config references
✗ VRM rendering
✗ lip sync
✗ motion generation
✗ image generation
✗ ComfyUI / RunningHub calls
✗ HTML frame rendering
✗ ffmpeg segment generation
✗ final video composition
✗ Streamlit UI
✗ VisualAlignmentReviewer
✗ TTSQualityReviewer
✗ FinalVideoReviewer
✗ full auto-fix loop
✗ persona acquisition
```

MVP2A is **not MVP2 as a whole**. MVP2 is split as:

```text
MVP2A = Presentation Planning
MVP2B = Asset & Render Preparation
MVP2C = Actual Media Generation / Composition
```

Any implementation that touches MVP2B or MVP2C functionality during this sprint is a scope violation unless it is only a schema stub required for imports.

---

## 2. Conceptual Correction

Earlier versions described MVP2 as `script → storyboard → assets`. Architecture v8 replaces that with:

```text
claims.json
→ narrative_plan.json
→ scenes.json
→ presentation_plan.json
→ asset_plan.json
→ media generation
→ composition
```

MVP2A only covers the first presentation-planning part.

The key distinction is:

```text
Persona = 誰在說
Style = 怎麼說
Presentation Profile = 畫面怎麼呈現
```

The default MVP2A presentation profile is:

```text
presenter_first_default
= 3D presenter is the primary narrative carrier
= assets are inserted only when helpful
= not every scene needs an asset
= not every second needs visual material
= background can be static and low-interference
= repeated background is allowed
```

This is a default profile, not a permanent limitation. The architecture must remain compatible with future profiles such as `slide_first_academic`, `figure_first_result_explainer`, `no_presenter_social_short`, or `character_variety_show`.

---

## 3. Deliverables

### 3.1 New / Updated Models

Create or update:

```text
p2s_core/models/presentation.py
p2s_core/models/scene.py
p2s_core/models/project_state.py
```

#### `presentation.py`

Must contain:

```python
class PresentationProfile(BaseModel): ...
class PresentationScene(BaseModel): ...
class PresentationPlan(BaseModel): ...
```

Minimum fields:

```python
class PresentationProfile(BaseModel):
    profile_id: str
    name: str
    description: str
    presenter_priority: Literal["low", "medium", "high"]
    default_background_mode: Literal[
        "static_clean", "static_thematic", "simple_gradient", "custom"
    ]
    require_asset_every_scene: bool = False
    asset_insertion_policy: Literal[
        "only_when_helpful", "balanced", "asset_rich"
    ] = "only_when_helpful"
    presenter_min_visibility_ratio: float = 0.6
    fullscreen_asset_allowed: bool = True
    fullscreen_asset_max_ratio: float = 0.25
    allow_repeated_background: bool = True
```

```python
class PresentationScene(BaseModel):
    scene_id: str
    scene_type: Literal[
        "presenter_only",
        "presenter_with_overlay",
        "asset_focus",
        "transition_or_card",
    ]
    presenter_mode: Literal[
        "speaking_on_camera",
        "speaking_with_overlay",
        "silent_presence",
        "minimized",
        "off_screen",
    ]
    visual_focus: Literal[
        "presenter",
        "supporting_asset",
        "split",
        "asset_fullscreen",
        "text_card",
    ]
    asset_policy: Literal["none", "optional", "required"]
    asset_type_hint: Literal[
        "none", "paper_figure", "diagram", "metaphor_image", "chart"
    ]
    background_mode: Literal[
        "static_clean", "static_thematic", "simple_gradient", "custom"
    ]
    estimated_asset_duration_sec: float | None = None
    render_notes: str | None = None
```

```python
class PresentationPlan(BaseModel):
    project_id: str
    profile_id: str
    scenes: list[PresentationScene]
    presenter_visibility_ratio: float
    asset_scene_ratio: float
    fullscreen_asset_ratio: float
    created_at: str
    quality_report: dict = {}
```

#### `scene.py`

Update `SceneDraft` and `Scene` to use `scene_id: str` and presentation fields.

Also update `ReviewResult.target_type` in `models/review.py` to include `"presentation"`:

```python
target_type: Literal[
    "claim", "script", "scene", "presentation",
    "visual", "tts", "subtitle", "segment", "final_video"
]
```

MVP2A reviewer results should use `target_type="presentation"` when reviewing at the stage level, and `target_type="scene"` when reviewing individual scenes.

Required MVP2A fields:

```python
scene_id: str
purpose: Literal["hook", "problem", "method", "result", "limitation", "takeaway", "transition"]
claim_ids: list[str]
voice_text: str
subtitle_text: str
target_duration_sec: float
presenter_mode: Literal[...]
visual_focus: Literal[...]
asset_policy: Literal["none", "optional", "required"]
asset_intent: str | None
asset_type_hint: Literal["none", "paper_figure", "diagram", "metaphor_image", "chart"]
background_mode: Literal["static_clean", "static_thematic", "simple_gradient", "custom"]
notes_for_render: str | None
risk_flags: list[str]
```

Deprecated fields may remain for compatibility:

```python
visual_type: str | None = None
visual_intent: str | None = None
character_presence: str | None = None
```

But MVP2A implementation must not depend on them.

### 3.2 New Presentation Profile Package

Create:

```text
p2s_core/presentation_profiles/
  presenter_first_default/
    presentation.yaml
    layout_rules.md
    examples/
      presenter_only.md
      presenter_with_overlay.md
      asset_focus.md
```

`presentation.yaml` minimum:

```yaml
profile_id: presenter_first_default
name: Presenter-first default
description: >
  以 3D 角色為主要敘事載體。背景固定且低干擾，素材圖片或圖表只在有助理解時插入。
  不要求每個 scene 都有圖片，也不要求素材每秒都存在。
presenter_priority: high
default_background_mode: static_clean
require_asset_every_scene: false
asset_insertion_policy: only_when_helpful
presenter_min_visibility_ratio: 0.6
fullscreen_asset_allowed: true
fullscreen_asset_max_ratio: 0.25
allow_repeated_background: true
```

### 3.3 New Services

Create:

```text
p2s_core/services/narrative_planning.py
p2s_core/services/presentation_planning.py
```

#### `NarrativePlanningService`

Input:

```text
claims.json
style profile
persona profile
project settings
```

Output:

```text
runs/{project_id}/narrative_plan.json
```

Minimum `narrative_plan.json` structure:

```json
{
  "project_id": "...",
  "target_duration_sec": 60,
  "language": "zh-TW",
  "audience": "general_science",
  "selected_claim_ids": ["claim_001", "claim_002"],
  "narrative_arc": [
    {
      "purpose": "hook",
      "claim_ids": ["claim_001"],
      "intent": "引出研究問題，但不誇大"
    },
    {
      "purpose": "method",
      "claim_ids": ["claim_002"],
      "intent": "用簡單直覺說明方法"
    }
  ],
  "omitted_claim_ids": [],
  "rationale": "...",
  "risk_flags": []
}
```

Rules:

1. Do not invent unsupported narrative points.
2. Each non-transition narrative item must reference at least one accepted claim.
3. Include limitation claim if one exists and has high importance.
4. Keep target duration realistic for 45–75 seconds.
5. Prefer fewer scenes with clear purpose over too many tiny scenes.

#### `PresentationPlanningService`

Input:

```text
claims.json
narrative_plan.json
persona profile
style profile
presentation profile
```

Output:

```text
runs/{project_id}/scenes.json
runs/{project_id}/presentation_plan.json
```

Rules:

1. Every non-transition scene must reference at least one valid `claim_id` from `claims.json`.
2. `transition` scenes may have `claim_ids = []`, but must not introduce new factual claims.
3. `voice_text` must not include unsupported claims.
4. `subtitle_text` must be shorter than `voice_text` and follow selected style subtitle rules.
5. Not every scene needs an asset.
6. `asset_policy = "none"` is valid, especially for hook, transition, and takeaway scenes.
7. If `asset_policy = "required"`, then `asset_intent` must be non-empty and `asset_type_hint != "none"`.
8. `presenter_first_default` should prefer presenter visibility and sparse asset usage.
9. `asset_fullscreen` scenes should be occasional, not dominant.
10. Background should default to `static_clean` unless style or presentation profile says otherwise.

### 3.4 New Reviewers

Create:

```text
p2s_core/reviewers/script_grounding.py
p2s_core/reviewers/style_rule.py
p2s_core/reviewers/presentation_structure.py
```

MVP2A reviewers should be deterministic where possible. LLM review may be added only if fake/stub tests remain possible without API access.

#### `ScriptGroundingReviewer`

Checks:

1. Each non-transition scene has at least one valid claim id.
2. Scene claim ids all exist in `claims.json`.
3. `voice_text` does not contain obvious unsupported numerical claims or absolute claims not found in linked claims.
4. Forbidden unsupported phrases such as `證明`, `完全解決`, `革命性`, `guarantee`, `proves` should be flagged unless present in linked claim text with explicit support.
5. Transition scenes must not introduce new factual claims.

Minimum output: a `list[ReviewResult]`. Stage-level summary must be placed in `PresentationReviewBundle.gate_decision.summary` or `quality_report`, not as a freeform string alongside the review list.

#### `StyleRuleReviewer`

Checks:

1. Forbidden phrases from selected style.
2. `voice_text` length per scene.
3. `subtitle_text` length per scene.
4. Subtitle should be shorter than voice text.
5. Hook should not use unsupported absolute claims.

MVP2A version can be purely rule-based.

#### `PresentationStructureReviewer`

Checks:

1. `presenter_visibility_ratio >= presentation_profile.presenter_min_visibility_ratio`, unless profile priority is not high.
2. `fullscreen_asset_ratio <= fullscreen_asset_max_ratio`.
3. If `require_asset_every_scene = false`, scenes should not all require assets.
4. If many scenes are `asset_fullscreen`, warn about presenter being suppressed.
5. If every scene has `asset_policy = required`, warn or fail under `presenter_first_default`.
6. Background modes should be consistent unless a scene explicitly justifies variation.

Recommended gate logic:

```text
critical fail:
- non-transition scene has no claim_id
- claim_id does not exist
- required asset scene has no asset_intent / asset_type_hint

high fail:
- unsupported factual phrase appears in voice_text
- presenter_visibility_ratio below hard threshold by large margin
- fullscreen_asset_ratio exceeds profile max by large margin

medium warning:
- subtitle too long
- too many optional assets
- background mode inconsistent
```

### 3.5 Arbiter for MVP2A

MVP2A should use a minimal arbiter gate named:

```text
presentation_gate
```

Status:

```text
gate_decision.status:
  pass          → project_state stage = done
  human_check   → project_state stage = needs_review
  reject        → project_state stage = rejected
```

No auto-fix loop in MVP2A.

Rules:

```text
if any critical fail:
  status = reject
elif any high fail:
  status = human_check
elif warnings only:
  status = pass with warnings
else:
  status = pass
```

Output file:

```text
runs/{project_id}/reviews/presentation_review_rev001.json
```

---

## 4. CLI Requirements

### 4.1 Existing Commands Must Continue Working

The following must remain valid:

```bash
python -m p2s_core.cli init path/to/paper.pdf
python -m p2s_core.cli run --stage extraction --project-id <id>
python -m p2s_core.cli run --stage claim_extraction --project-id <id>
python -m p2s_core.cli status --project-id <id>
```

### 4.2 New Stage Commands

MVP2A adds:

```bash
python -m p2s_core.cli run --stage narrative_planning --project-id <id>
python -m p2s_core.cli run --stage presentation_planning --project-id <id>
```

Recommended behavior:

```text
run --stage narrative_planning
- requires claim_extraction done
- reads claims.json
- writes narrative_plan.json
- updates stages.narrative_planning

run --stage presentation_planning
- requires narrative_planning done
- reads claims.json + narrative_plan.json
- writes scenes.json + presentation_plan.json
- runs MVP2A reviewers
- writes reviews/presentation_review_rev001.json
- updates stages.presentation_planning
```

### 4.3 Dependency Enforcement

If the user runs:

```bash
python -m p2s_core.cli run --stage presentation_planning --project-id <id>
```

without `claim_extraction` and `narrative_planning` marked as `done`, CLI must fail gracefully with a clear message:

```text
Cannot run presentation_planning: required stage narrative_planning is not done.
Run: p2s run --stage narrative_planning --project-id <id>
```

No stack trace for expected dependency errors.

---

## 5. Project State Updates

### 5.1 New Stage Keys

Add stage records:

```json
"stages": {
  "narrative_planning": {
    "status": "pending",
    "started_at": null,
    "finished_at": null,
    "output_paths": [],
    "error": null,
    "revision_count": 0
  },
  "presentation_planning": {
    "status": "pending",
    "started_at": null,
    "finished_at": null,
    "output_paths": [],
    "error": null,
    "revision_count": 0
  }
}
```

### 5.2 Output Paths

After success:

```json
"stages": {
  "narrative_planning": {
    "status": "done",
    "output_paths": ["narrative_plan.json"]
  },
  "presentation_planning": {
    "status": "done",
    "output_paths": [
      "scenes.json",
      "presentation_plan.json",
      "reviews/presentation_review_rev001.json"
    ]
  }
}
```

If review gate returns `human_check`, stage status should be:

```text
needs_review
```

If review gate returns `reject`, stage status should be:

```text
rejected
```

---

## 6. Output File Contracts

### 6.1 `narrative_plan.json`

Must contain:

```text
project_id
target_duration_sec
language
audience
selected_claim_ids
narrative_arc
omitted_claim_ids
rationale
risk_flags
created_at
```

Every `narrative_arc` item must contain:

```text
purpose
claim_ids
intent
```

### 6.2 `scenes.json`

Must contain a list or object containing `SceneDraft` records.

Recommended wrapper:

```json
{
  "project_id": "...",
  "scenes": [
    {
      "scene_id": "scene_001",
      "purpose": "hook",
      "claim_ids": ["claim_001"],
      "voice_text": "...",
      "subtitle_text": "...",
      "target_duration_sec": 6.0,
      "presenter_mode": "speaking_on_camera",
      "visual_focus": "presenter",
      "asset_policy": "none",
      "asset_intent": null,
      "asset_type_hint": "none",
      "background_mode": "static_clean",
      "notes_for_render": null,
      "risk_flags": []
    }
  ],
  "created_at": "..."
}
```

### 6.3 `presentation_plan.json`

Must contain:

```text
project_id
profile_id
scenes
presenter_visibility_ratio
asset_scene_ratio
fullscreen_asset_ratio
created_at
quality_report
```

### 6.4 `presentation_review_rev001.json`

Use a `PresentationReviewBundle` structure, modeled after `ClaimReviewBundle` from MVP1 for consistency:

```python
class PresentationReviewBundle(BaseModel):
    project_id: str
    target_stage: Literal["presentation_planning"] = "presentation_planning"
    reviews: list[ReviewResult]
    gate_decision: GateDecision
    created_at: str
```

Serialized example:

```json
{
  "project_id": "...",
  "target_stage": "presentation_planning",
  "reviews": [
    {
      "reviewer": "ScriptGroundingReviewer",
      "pass_gate": true,
      "severity": "low",
      "findings": [],
      "suggested_fixes": []
    },
    {
      "reviewer": "StyleRuleReviewer",
      "pass_gate": true,
      "severity": "low",
      "findings": [],
      "suggested_fixes": []
    },
    {
      "reviewer": "PresentationStructureReviewer",
      "pass_gate": true,
      "severity": "low",
      "findings": [],
      "suggested_fixes": []
    }
  ],
  "gate_decision": {
    "status": "pass",
    "summary": "...",
    "blocking_issues": [],
    "warnings": []
  },
  "created_at": "..."
}
```

> **一致性說明**：`PresentationReviewBundle` 的欄位名稱（`reviews` / `gate_decision`）與 MVP1 的 `ClaimReviewBundle` 保持一致。`gate_decision.status` 的值域為 `pass` / `human_check` / `reject`，對應 project_state 的 `done` / `needs_review` / `rejected`。

---

## 7. Testing Plan

### Tier 0 — Schema Tests

Add or update:

```text
tests/test_schema.py
tests/test_presentation_schema.py
```

Required tests:

1. `SceneDraft` accepts `scene_id="scene_001"`.
2. `SceneDraft` rejects invalid `presenter_mode`.
3. `SceneDraft` rejects invalid `visual_focus`.
4. `SceneDraft` rejects invalid `asset_policy`.
5. `PresentationProfile` roundtrip JSON serialization works.
6. `PresentationPlan` computes or stores ratios correctly.
7. Deprecated `visual_type` may be `None` without failure.
8. Existing `test_scene_roundtrip` fixture updated from `scene_id=1` to `scene_id="scene_001"`.
9. Existing `test_scene_visual_type_consistency` renamed to `test_scene_presentation_fields_consistency`.

### Tier 1 — Deterministic Service Tests

Use fake claims and fake LLM outputs.

Add:

```text
tests/test_narrative_planning.py
tests/test_presentation_planning.py
```

Required tests:

1. Narrative plan uses only claim ids from claims.json.
2. Presentation planning produces scene ids as strings.
3. Non-transition scenes all have claim ids.
4. Transition scenes may have empty claim ids.
5. `asset_policy="required"` requires `asset_intent` and non-`none` `asset_type_hint`.
6. `presenter_first_default` does not require every scene to have an asset.
7. Static background repeated across scenes is valid.

### Tier 2 — Reviewer Tests

Add:

```text
tests/test_script_grounding_reviewer.py
tests/test_style_rule_reviewer.py
tests/test_presentation_structure_reviewer.py
```

Required bad cases:

1. Scene references non-existent claim id → critical fail.
2. Non-transition scene has no claim id → critical fail.
3. Scene uses forbidden phrase `證明` unsupported by claim → high fail.
4. Subtitle too long → warning or medium fail.
5. Every scene has `asset_policy="required"` under `presenter_first_default` → warning/high depending severity.
6. Fullscreen asset ratio exceeds max → high fail.
7. Required asset has no `asset_intent` → critical fail.

### Tier 3 — Pipeline / CLI Smoke Tests

Add:

```text
tests/test_mvp2a_pipeline_smoke.py
```

Required smoke flow with fake LLM:

```text
existing project with extracted_text.md + claims.json
→ run narrative_planning
→ run presentation_planning
→ assert files exist:
   narrative_plan.json
   scenes.json
   presentation_plan.json
   reviews/presentation_review_rev001.json
→ assert project_state stages updated
```

No Tier 3 test may require real OpenAI API.

### Tier 4 — Manual Real Paper Smoke

Manual, not CI:

```bash
python -m p2s_core.cli run --stage narrative_planning --project-id <real_project>
python -m p2s_core.cli run --stage presentation_planning --project-id <real_project>
python -m p2s_core.cli status --project-id <real_project>
```

Manual acceptance:

1. Outputs are created.
2. At least 5 scenes are generated for a typical paper.
3. Every non-transition scene references valid claims.
4. Not every scene has an asset.
5. Presenter-first profile is reflected in presentation ratios.
6. Review file clearly explains pass / needs_review / reject.

---

## 8. Must / Should / Deferred

### 8.1 Must

```text
M1. Update SceneDraft / Scene schema to v8 presentation fields.
M2. Add PresentationProfile / PresentationScene / PresentationPlan schema.
M3. Add presenter_first_default presentation profile package.
M4. Add narrative_planning stage.
M5. Add presentation_planning stage.
M6. Output narrative_plan.json.
M7. Output scenes.json.
M8. Output presentation_plan.json.
M9. Output reviews/presentation_review_rev001.json.
M10. Add ScriptGroundingReviewer.
M11. Add StyleRuleReviewer.
M12. Add PresentationStructureReviewer.
M13. Enforce claim_id validity.
M14. Enforce no required asset without asset intent/type.
M15. Update scene_id tests from int to str.
M16. Replace visual_type consistency test with presentation field consistency test.
M17. CLI supports narrative_planning and presentation_planning.
M18. All tests pass without real API access.
```

### 8.2 Should

```text
S1. Use style prompt examples for scene generation.
S2. Use persona prompt profile lightly in voice_text generation.
S3. Estimate total duration from scene target durations.
S4. Add quality_report to presentation_plan.json.
S5. Add clear reviewer summaries for human debugging.
S6. Add fake LLM fixtures for stable regression tests.
S7. Add one real-paper manual smoke report.
```

### 8.3 Deferred

```text
D1. Auto-fix loop.
D2. Full Devil's Advocate reviewer.
D3. PersonaConsistencyReviewer.
D4. StyleConsistencyReviewer LLM-based version.
D5. VisualAlignmentReviewer.
D6. TTS plan details beyond placeholders.
D7. Actual TTS generation.
D8. Actual image generation.
D9. Actual VRM rendering.
D10. Streamlit UI.
D11. asset_plan.json.
D12. storyboard migration beyond deprecated field compatibility.
```

---

## 9. Hard Gates / Failure Conditions

MVP2A is not complete if any of these are true:

```text
F1. Tests require real OpenAI / network access to pass.
F2. Existing MVP0/MVP1 tests fail and are not explicitly migrated due to v8 breaking changes.
F3. SceneDraft still requires scene_id: int.
F4. Non-transition scenes can pass with missing or invalid claim_ids.
F5. `visual_type` remains the primary presentation decision field.
F6. presentation_plan.json is not generated.
F7. presentation_review_rev001.json is not generated.
F8. p2s run --stage presentation_planning can run before narrative_planning.
F9. MVP2A code calls TTS, ComfyUI, ffmpeg, Playwright, or VRM renderer.
F10. asset_plan.json is implemented as a full MVP2B artifact during MVP2A.
F11. The reviewer gate ignores critical grounding failures.
F12. The pipeline crashes on expected dependency errors instead of returning a clear CLI message.
```

---

## 10. Migration Tasks from v7/v8

MVP2A Day 1 must handle architecture migration conflicts:

### C-001 — `scene_id: int → str`

Action:

```text
Update scene fixtures and schemas:
scene_id=1 → scene_id="scene_001"
```

### C-002 — `visual_type` consistency test obsolete

Action:

```text
Rename:
test_scene_visual_type_consistency
→ test_scene_presentation_fields_consistency
```

New test should check consistency of:

```text
presenter_mode
visual_focus
asset_policy
asset_type_hint
background_mode
```

between `SceneDraft`, `Scene`, and `PresentationScene` where applicable.

### C-003 — `storyboard_planning → asset_preparation`

Action:

```text
Do not implement full C-003 in MVP2A.
Only ensure MVP2A does not introduce new `storyboard_planning` references.
Full replacement belongs to MVP2B Day 1.
```

### C-004 — old stage names in docs

Already handled in Architecture v8 cleanup. No code action unless old strings exist in current codebase.

---

## 11. Suggested Day-by-Day Plan

### Day 1 — Schema Migration

Tasks:

1. Add `models/presentation.py`.
2. Update `SceneDraft` / `Scene` fields.
3. Migrate `scene_id` fixtures to strings.
4. Rename visual type consistency tests.
5. Add `presenter_first_default/presentation.yaml`.

Exit criteria:

```text
pytest tests/test_schema.py tests/test_presentation_schema.py
```

passes.

### Day 2 — Narrative Planning

Tasks:

1. Add `NarrativePlanningService`.
2. Add `narrative_plan.json` schema or wrapper.
3. Add fake LLM output parsing.
4. Add CLI stage `narrative_planning`.
5. Add project_state stage update.

Exit criteria:

```text
p2s run --stage narrative_planning
```

works on fake project.

### Day 3 — Presentation Planning

Tasks:

1. Add `PresentationPlanningService`.
2. Generate `scenes.json` from claims + narrative plan.
3. Generate `presentation_plan.json`.
4. Compute presentation ratios.
5. Enforce required asset field rules.

Exit criteria:

```text
scenes.json + presentation_plan.json are created and schema-valid.
```

### Day 4 — MVP2A Reviewers

Tasks:

1. Add `ScriptGroundingReviewer`.
2. Add `StyleRuleReviewer`.
3. Add `PresentationStructureReviewer`.
4. Add minimal `presentation_gate` arbiter.
5. Write `presentation_review_rev001.json`.

Exit criteria:

```text
bad cases fail clearly; good fake case passes.
```

### Day 5 — Pipeline Smoke + Manual Test

Tasks:

1. Add end-to-end fake LLM smoke test.
2. Run with at least one real MVP1 project.
3. Fix project_state edge cases.
4. Write `MVP2A_STATUS.md` draft.

Exit criteria:

```text
All automated tests pass.
Manual smoke produces narrative_plan.json, scenes.json, presentation_plan.json, presentation_review_rev001.json.
New test count: Tier 0 ≥ 9, Tier 1 ≥ 7, Tier 2 ≥ 7, Tier 3 ≥ 4（共 ≥ 27 新增 tests，MVP0/MVP1 原有 tests 全數保留）
```

---

## 12. Acceptance Checklist

MVP2A is accepted only when:

```text
□ Existing MVP0/MVP1 tests pass or are intentionally migrated with explanation.
□ New presentation schema tests pass.
□ New narrative planning tests pass.
□ New presentation planning tests pass.
□ New reviewer tests pass.
□ Fake LLM pipeline smoke passes without network.
□ Manual real-paper smoke completed.
□ `narrative_plan.json` exists.
□ `scenes.json` exists.
□ `presentation_plan.json` exists.
□ `reviews/presentation_review_rev001.json` exists.
□ project_state has narrative_planning and presentation_planning stages.
□ Non-transition scenes all reference valid claims.
□ At least one presenter-only or presenter-focused scene exists under presenter_first_default.
□ Not every scene is forced to have an asset under presenter_first_default.
□ No TTS / image / VRM / ffmpeg / Streamlit implementation was added.
□ `MVP2A_STATUS.md` records completion, test count, manual smoke, and open issues.
```

---

## 13. Expected Final State

After MVP2A, a project run directory should look like:

```text
runs/{project_id}/
  source.pdf
  project_state.json
  extracted_text.md
  claims.json
  narrative_plan.json
  scenes.json
  presentation_plan.json
  reviews/
    claim_review_rev001.json
    presentation_review_rev001.json
```

It should not yet contain MVP2B/2C outputs such as:

```text
asset_plan.json
audio/
assets/
frames/
segments/
final/output.mp4
```

---

## 14. One-Sentence Summary

> MVP2A turns grounded claims into an inspectable, claim-grounded, presenter-aware presentation plan; it does not generate media.
