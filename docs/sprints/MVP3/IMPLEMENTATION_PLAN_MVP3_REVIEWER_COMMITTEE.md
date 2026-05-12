# IMPLEMENTATION PLAN — P2S MVP3：Reviewer Committee / Final Review Gate

> 文件定位：本文件是 **MVP3 sprint contract**，可直接交給 coding agent / Codex / Claude Code 作為開工依據。  
> 本階段目標是建立 P2S 的 **reviewer committee / final review gate**，讓已產生的 script、asset plan、media artifacts 與 final video 可以被結構化審查。  
> **MVP3 先做 report + gate，不做完整 auto-fix loop，不做 Streamlit UI，不做 full media generation。**

---

## 0. 當前前提

目前 P2S 已完成：

```text
MVP0        → schema / state / CLI / basic extraction
MVP1        → claim extraction / evidence mapping / deterministic reviewers
MVP2A       → narrative planning / presentation planning
MVP2A-2     → LLM quality rewrite / active_scene_source
MVP2B       → asset_preparation / asset_plan.json
HARDEN-1    → extraction / evidence / figure metadata hardening
MVP2C-thin  → minimal playable video pipeline
HARDEN-3    → media quality / composition report-first gate
```

目前已有關鍵 artifacts：

```text
runs/{project_id}/claims.json
runs/{project_id}/reviews/claim_review_rev001.json
runs/{project_id}/narrative_plan.json
runs/{project_id}/scenes.json
runs/{project_id}/scenes_rewritten.json              # optional
runs/{project_id}/presentation_plan.json
runs/{project_id}/asset_plan.json
runs/{project_id}/media_generation_report.json
runs/{project_id}/media_quality_report.json
runs/{project_id}/final/output.mp4
runs/{project_id}/project_state.json
```

HARDEN-3 已確認：

```text
- media_quality_check stage exists
- media_quality_report.json is produced
- final/output.mp4 exists and passes basic media quality gate
- report-only behavior is preserved
- full regression passed
```

因此可以進入：

```text
MVP3: Reviewer Committee / Final Review Gate
```

---

## 1. MVP3 核心目標

MVP3 的核心目標是讓 P2S 不只「能生成影片」，而是能對生成結果做結構化審查：

```text
claims.json
+ active scene source
+ asset_plan.json
+ media_quality_report.json
+ final/output.mp4
→ final_review.json
→ GateDecision
```

MVP3 要回答：

```text
1. 最終影片的旁白內容是否仍忠於 claims / evidence？
2. 每個 scene 的 voice_text / subtitle_text 是否有支持來源？
3. 視覺素材是否和該 scene 的意圖一致？
4. subtitle / media quality 是否有 blocking 問題？
5. 是否存在 hype、unsupported claim、錯誤類比或觀眾可能誤解的地方？
6. 最終 gate 應該是 pass / revise / human_check / reject？
```

MVP3 的完成標誌：

```text
runs/{project_id}/reviews/final_review_rev001.json exists
runs/{project_id}/reviews/final_gate_decision_rev001.json exists
project_state.stages.final_review.status == "done" or "needs_review"
```

---

## 2. Non-goals：MVP3 明確不做

MVP3 不是 full auto-repair 系統，也不是 UI sprint。

禁止在本 sprint 中實作：

```text
- Streamlit / React inspection UI
- full auto-fix loop
- automatic subtitle rewrite
- automatic scene rewrite
- automatic visual regeneration
- automatic media regeneration
- ComfyUI / RunningHub image generation
- VRM rendering
- lip sync / motion generation
- new video composition logic
- human study / evaluation runner
```

允許實作：

```text
- deterministic reviewers
- optional LLM reviewers behind existing LLMService, if already supported
- structured review reports
- final gate decision
- blocking issue aggregation
- reviewer calibration fixtures
- CLI stage integration
```

MVP3 第一版建議以 **deterministic + existing data** 為主。若使用 LLM reviewer，必須明確標為 optional / provider-dependent，不得讓 unit tests 依賴 real API key。

---

## 3. 設計原則

### 3.1 Reviewer committee is structured, not debate chat

MVP3 不做自由多代理辯論。每個 reviewer 都有固定輸入、固定輸出、固定 rubric。

```text
Correct:
  PaperFidelityReviewer checks claim support.
  VisualAlignmentReviewer checks scene visual consistency.
  FinalVideoReviewer aggregates media quality and artifact completeness.
  DevilAdvocate flags hype / misleading claims.
  Arbiter produces GateDecision.

Incorrect:
  Let agents chat freely and vote.
  Use one vague 1–10 score.
  Let reviewer outputs overwrite artifacts.
```

### 3.2 Factuality and grounding are veto-capable

如果 Paper Fidelity / Claim Evidence 類 reviewer 發現 high severity unsupported claim，不能被其他分數平均掉。

```text
unsupported factual claim
→ blocking issue
→ gate status = reject or human_check
```

### 3.3 Report-first, no auto-fix in MVP3

MVP3 的第一版只產生 report 和 gate decision。

```text
generate / load artifacts
→ review
→ aggregate
→ write final_review
→ write gate decision
```

不自動改稿、不自動重生圖、不自動重跑影片。

### 3.4 Preserve prior artifacts

MVP3 不修改以下 artifacts：

```text
claims.json
scenes.json
scenes_rewritten.json
presentation_plan.json
asset_plan.json
media_quality_report.json
final/output.mp4
```

它只新增 review outputs。

---

## 4. 新增 / 修改檔案清單

### 4.1 Models

新增或擴充：

```text
p2s_core/models/final_review.py
```

建議新增 schema：

```text
ReviewerFinding
ReviewerSummary
FinalReviewBundle
FinalGateDecision
```

若既有 `ReviewResult` / `GateDecision` schema 足夠，應優先復用；新增 schema 只負責 MVP3 bundle-level 包裝。

### 4.2 Reviewers

新增或強化：

```text
p2s_core/reviewers/final_video.py
p2s_core/reviewers/visual_alignment.py
p2s_core/reviewers/subtitle_readability.py
p2s_core/reviewers/devil_advocate.py
p2s_core/reviewers/final_arbiter.py
```

復用既有：

```text
p2s_core/reviewers/claim_evidence.py
p2s_core/reviewers/paper_fidelity.py
p2s_core/reviewers/style_rule.py
```

### 4.3 Services

新增：

```text
p2s_core/services/final_review_service.py
p2s_core/services/review_bundle_writer.py
```

可選：

```text
p2s_core/services/reviewer_calibration.py
```

### 4.4 Pipeline / CLI

修改：

```text
p2s_core/pipelines/paper_summary.py
p2s_core/cli.py
p2s_core/models/project_state.py
```

目標：

```text
- 支援 `run --stage final_review`
- final_review requires composition == done
- final_review optionally requires media_quality_check == done
- status 顯示 final_review
- migration 不重設已完成 stage
```

建議依賴：

```text
final_review requires composition == done
final_review strongly prefers media_quality_check == done
```

Policy：

```text
if media_quality_report.json missing:
  warning only in first MVP3 version
  FinalVideoReviewer should mark media_quality_missing warning
```

### 4.5 Tests

新增：

```text
tests/test_final_review_schema.py
tests/test_final_video_reviewer.py
tests/test_visual_alignment_reviewer.py
tests/test_devil_advocate_reviewer.py
tests/test_final_arbiter.py
tests/test_mvp3_final_review_pipeline.py
tests/test_reviewer_prompt_injection_guards.py
tests/test_paper_fidelity_final_reviewer_adapter.py
```

### 4.6 Fixtures / Golden Data

新增：

```text
tests/golden/final_review/
  good_final_project/
  unsupported_claim_scene.json
  overhyped_scene.json
  visual_mismatch_scene.json
  missing_media_quality_report/
  prompt_injection_scene.json
```

若不使用 real video fixtures，使用 minimal JSON artifact fixtures 即可。

### 4.7 Docs

新增：

```text
docs/sprints/MVP3/IMPLEMENTATION_PLAN_MVP3_REVIEWER_COMMITTEE.md
docs/sprints/MVP3/MVP3_STATUS.md
docs/sprints/MVP3/reports/MVP3_FINAL_REVIEW_SMOKE.md
```

---

## 5. Schema 設計

### 5.1 ReviewerFinding

```python
class ReviewerFinding(BaseModel):
    finding_id: str
    reviewer: str
    target_type: Literal[
        "claim",
        "scene",
        "asset_plan",
        "visual",
        "subtitle",
        "audio",
        "segment",
        "final_video",
        "project",
    ]
    target_id: str
    severity: Literal["info", "low", "medium", "high", "critical"]
    category: Literal[
        "unsupported_claim",
        "missing_evidence",
        "overhype",
        "limitation_missing",
        "visual_mismatch",
        "subtitle_readability",
        "media_quality",
        "fallback_quality",
        "style_violation",
        "prompt_injection",
        "artifact_missing",
        "other",
    ]
    message: str
    evidence_refs: list[str] = []
    suggested_fix: str | None = None
    blocking: bool = False
```

---

### 5.2 ReviewerSummary

```python
class ReviewerSummary(BaseModel):
    reviewer: str
    pass_gate: bool
    score: float | None = None
    findings: list[ReviewerFinding] = []
    blocking_count: int = 0
    warning_count: int = 0
    created_at: str
    reviewer_version: str = "mvp3_v1"
```

---

### 5.3 FinalReviewBundle

```python
class FinalReviewBundle(BaseModel):
    project_id: str
    review_id: str
    active_scene_source: str
    final_video_path: str | None = None
    reviewer_summaries: list[ReviewerSummary]
    media_quality_report_path: str | None = None
    total_findings: int
    blocking_issues: list[ReviewerFinding] = []
    warnings: list[ReviewerFinding] = []
    created_at: str
    version: str = "mvp3_v1"
```

輸出：

```text
runs/{project_id}/reviews/final_review_rev001.json
```

---

### 5.4 FinalGateDecision

```python
class FinalGateDecision(BaseModel):
    project_id: str
    gate_name: str = "final_review_gate"
    review_id: str
    status: Literal["pass", "revise", "human_check", "reject"]
    blocking_issues: list[ReviewerFinding] = []
    warning_count: int = 0
    reviewer_statuses: dict[str, str] = {}
    rationale: str
    created_at: str
    version: str = "mvp3_v1"
```

輸出：

```text
runs/{project_id}/reviews/final_gate_decision_rev001.json
```

---

## 6. Reviewer design

### 6.1 PaperFidelityFinalReviewer

Purpose：

```text
Check whether final scene voice/subtitle content remains faithful to paper claims and evidence.
```

Inputs：

```text
claims.json
active scene source
claim_review output
```

Rules：

```text
- every non-transition scene should have claim_ids unless explicitly allowed
- scene voice_text should not introduce unsupported factual claims
- limitation scenes must not be dropped if claims include explicit limitations
- high severity unsupported factual claim becomes blocking
```

MVP3 implementation：

```text
PaperFidelityFinalReviewer 是 MVP3 的 adapter wrapper。
內部呼叫既有 ClaimEvidenceReviewer / PaperFidelityReviewer，
負責把這兩個 reviewer 的 ClaimReviewBundle findings 轉換成 ReviewerFinding list，
並包裝成 ReviewerSummary 回傳給 FinalArbiter。

此 wrapper 和 ClaimReviewBundle → ReviewerFinding 的轉換邏輯必須有獨立 test coverage，
不得讓 MVP1 格式的 output 直接進入 FinalReviewBundle 而繞過 MVP3 schema。

Severity mapping 建議（可調整）：
  ClaimReviewBundle failed finding  → ReviewerFinding blocking=True, severity="high"
  ClaimReviewBundle warning finding → ReviewerFinding blocking=False, severity="medium"
  ClaimReviewBundle pass finding    → ReviewerFinding blocking=False, severity="info"
```

---

### 6.2 VisualAlignmentReviewer

Purpose：

```text
Check whether visual plan / generated visual source is compatible with scene intent.
```

Inputs：

```text
asset_plan.json
media_metadata/visuals.json
media_quality_report.json
figures.json optional
```

Rules：

```text
- paper_figure with selected_figure_ids and image_path is acceptable
- paper_figure fallback to text_card is warning, not fail
- diagram/metaphor/chart fallback to text_card is warning in MVP2C-thin
- visual missing is blocking
- visual source contradicting scene asset intent is high severity if detectable deterministically
```

MVP3 first-pass deterministic checks：

```text
- artifact exists
- asset_source / fallback reason consistent with media metadata
- selected paper figure ids exist in figures.json when used
- missing visual metadata becomes warning or blocking depending artifact existence
```

---

### 6.3 SubtitleReadabilityFinalReviewer

Purpose：

```text
Reuse HARDEN-3 subtitle readability results and flag blocking subtitle issues.
```

Inputs：

```text
media_quality_report.json
asset_plan.json
```

Rules：

```text
- safe_area_ok == false → blocking
- empty subtitle → warning unless scene purpose permits
- too_long subtitle → warning
```

No rewrite in MVP3.

---

### 6.4 FinalVideoReviewer

Purpose：

```text
Check final/output.mp4 and media_quality_report summary.
```

Inputs：

```text
media_quality_report.json
final/output.mp4
media_generation_report.json
```

Rules：

```text
- media_quality_report.pass_gate == false → blocking
- final video missing → critical blocking
- fallback_quality.quality_level == minimal → high warning, not automatic fail
- loudness unavailable → warning
```

---

### 6.5 DevilAdvocateReviewer

Purpose：

```text
Find overhype, misleading wording, unsupported absolutist claims, and prompt-injection style content.
```

Inputs：

```text
active scene source
style forbidden phrases
claims.json
```

First-pass deterministic checks：

```text
- forbidden hype phrases
- absolute claims: "prove", "guarantee", "完全解決", "革命性", "顛覆", "絕對"
- prompt injection patterns: "ignore previous", "給我 pass", "reviewer", "system prompt"
```

Policy：

```text
- prompt injection pattern → blocking high severity
- hype phrase → warning or blocking depending phrase and context
- deterministic first; optional LLM expansion later
```

---

### 6.6 StyleRuleFinalReviewer

Purpose：

```text
Run style rule checks one final time on active scene source.
```

Inputs：

```text
active scene source
style profile / forbidden_phrases.txt
```

Rules：

```text
- forbidden phrase → warning or blocking if overhype factual phrase
- subtitle too long → delegate to SubtitleReadabilityFinalReviewer
- style issue alone should not reject unless it creates factual risk
```

---

### 6.7 FinalArbiter

Purpose：

```text
Aggregate reviewer summaries into FinalGateDecision.
```

Rules：

```text
if any finding with blocking=True and severity=="critical":
  status = "reject"

elif any finding with blocking=True:
  status = "human_check"

elif any reviewer pass_gate == false:
  status = "human_check"

elif warnings exist:
  status = "pass"

else:
  status = "pass"
```

說明：`blocking` 欄位是 veto trigger，`severity` 決定升到 `reject` 還是 `human_check`。
`severity="medium"` 且 `blocking=True` 的 finding 會觸發 `human_check`，不會靜默通過。
不要以 severity 作為第一層判斷，否則 `blocking=True` + `severity="medium"` 會被 `elif warnings exist → pass` 吞掉。

MVP3 does not auto-revise. Therefore:

```text
status = "revise" is reserved but normally not emitted in MVP3 v1.
```

Rationale must explain:

```text
- why pass / human_check / reject
- number of blocking issues
- which reviewer caused the gate decision
```

---

## 7. Execution rules

### 7.1 Input resolution

Required：

```text
project_state.json
claims.json
asset_plan.json
final/output.mp4
```

Required or warning：

```text
active scene source：
  讀取 project_state.active_scene_source 指向的檔案
  若該檔案不存在：warning + fallback to scenes.json
  若 scenes.json 也不存在：hard fail
```

Recommended：

```text
media_quality_report.json
media_generation_report.json
figures.json
style package
```

If `media_quality_report.json` is missing：

```text
warning only in MVP3 v1
FinalVideoReviewer should emit media_quality_missing warning
```

---

### 7.2 Active scene source policy

MVP3 must read active scene source strictly through `project_state.active_scene_source`，與 MVP2B / MVP2C 合約一致：

```text
1. 讀取 project_state.active_scene_source
2. 讀取其指向的檔案
   → 若檔案存在：使用
   → 若檔案不存在：warning + fallback to scenes.json（並記入 final_review bundle warnings）

禁止在 active_scene_source 之外獨立檢查 scenes_rewritten.json 是否存在。
```

理由：`project_state.active_scene_source` 是 MVP2B gate 的決策結果，是唯一可信來源。
若 MVP3 自行推斷「scenes_rewritten.json 存在就用它」，可能讀到未通過 gate 的版本，
違反「active source 由 gate decision 決定」的合約原則。

If requested active scene source is missing but fallback exists：

```text
warning in final_review bundle
```

Do not hardcode `scenes.json` as primary source.

---

### 7.3 Review output revision numbering

Review outputs must not overwrite old outputs.

Use revision numbering：

```text
reviews/final_review_rev001.json
reviews/final_gate_decision_rev001.json
```

If files already exist：

```text
write rev002, rev003, ...
```

---

### 7.4 Stage status policy

`final_review` stage status：

```text
pass gate status == pass
  → project_state.stages.final_review.status = "done"

gate status == human_check
  → project_state.stages.final_review.status = "needs_review"

gate status == reject
  → project_state.stages.final_review.status = "needs_review"
  → do not delete final video
```

MVP3 does not set `rejected` stage status automatically, because no repair loop exists yet.

---

## 8. Validation / quality gates

### 8.1 Hard fail

```text
- project_state.json missing
- claims.json missing
- asset_plan.json missing
- active scene source missing
- final/output.mp4 missing
- schema validation failure
```

### 8.2 Warning only

```text
- media_quality_report.json missing
- media_generation_report.json missing
- figures.json missing
- requested active_scene_source missing but fallback used
- fallback visual used
- loudness unavailable
- style package missing, style reviewer skipped
```

### 8.3 Gate status semantics

```text
pass:
  no blocking issues; warnings may exist

human_check:
  blocking issue exists but artifact may still be inspectable;
  user / developer should inspect before proceeding

reject:
  critical factuality / prompt injection / artifact integrity issue;
  pipeline should not treat output as publishable
```

---

## 9. Tests

### 9.1 Schema tests

File：

```text
tests/test_final_review_schema.py
```

Must test：

```text
- ReviewerFinding roundtrip
- ReviewerSummary roundtrip
- FinalReviewBundle roundtrip
- FinalGateDecision roundtrip
```

---

### 9.2 Final video reviewer tests

File：

```text
tests/test_final_video_reviewer.py
```

Must test：

```text
- media_quality_report.pass_gate true → reviewer pass
- media_quality_report.pass_gate false → blocking finding
- final/output.mp4 missing → critical blocking
- loudness unavailable warning is preserved
- fallback_quality minimal → warning, not automatic reject
```

---

### 9.3 Visual alignment reviewer tests

File：

```text
tests/test_visual_alignment_reviewer.py
```

Must test：

```text
- existing visual metadata passes
- missing visual artifact blocks
- paper_figure fallback to text_card warns
- selected_figure_id missing from figures.json warns or blocks according to artifact existence
- diagram/metaphor/chart fallback warns in MVP2C-thin
```

---

### 9.4 Devil advocate tests

File：

```text
tests/test_devil_advocate_reviewer.py
```

Must test：

```text
- overhype phrase warning
- absolute unsupported phrase blocking when configured
- prompt injection pattern blocking
- normal scene passes
```

---

### 9.5 Arbiter tests

File：

```text
tests/test_final_arbiter.py
```

Must test：

```text
- no blocking issues → pass
- blocking=True + severity="critical" → reject
- blocking=True + severity="high" → human_check
- blocking=True + severity="medium" → human_check（不可靜默通過）
- blocking=True + severity="low" → human_check
- reviewer pass_gate false → human_check
- warnings only, no blocking → pass
- mixed: blocking critical + other warnings → reject（critical veto 優先）
```

---

### 9.6 Pipeline tests

File：

```text
tests/test_mvp3_final_review_pipeline.py
```

Must test：

```text
- run --stage final_review writes final_review_rev001.json
- run --stage final_review writes final_gate_decision_rev001.json
- revision numbering writes rev002 if rev001 exists
- stage status done when gate pass
- stage status needs_review when human_check/reject
- missing final video fails clearly
- active_scene_source fallback warning
```

---

### 9.7 Prompt injection guard tests

File：

```text
tests/test_reviewer_prompt_injection_guards.py
```

Must test：

```text
- scene text containing "ignore previous instructions" is treated as content
- scene text asking reviewer to give pass is flagged
- reviewer system prompt is not modified by candidate content
```

Even if MVP3 uses deterministic checks, keep these fixtures for future LLM reviewer safety.

---

## 10. Manual smoke plan

Use an accepted MVP2C-thin + HARDEN-3 project：

```bash
.\.venv-win\Scripts\python.exe -m p2s_core.cli status --project mvp2c_thin_smoke
.\.venv-win\Scripts\python.exe -m p2s_core.cli run --stage final_review --project mvp2c_thin_smoke
```

Expected output：

```text
runs/mvp2c_thin_smoke/reviews/final_review_rev001.json
runs/mvp2c_thin_smoke/reviews/final_gate_decision_rev001.json
```

Expected status：

```text
final_review: done
```

Expected gate：

```text
status: pass
```

If warnings exist：

```text
gate may still pass
warnings must be visible in review bundle
```

Smoke report：

```text
docs/sprints/MVP3/reports/MVP3_FINAL_REVIEW_SMOKE.md
```

---

## 11. Day-by-day sprint plan

### Day 1：Schemas and bundle writer

```text
- Add final review schemas.
- Add schema exports.
- Add roundtrip tests.
- Add revision-numbered output writer.
```

Verification：

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/test_final_review_schema.py -v
```

---

### Day 2：PaperFidelityFinalReviewer adapter + FinalVideoReviewer

```text
- Implement PaperFidelityFinalReviewer as adapter wrapper.
- Map ClaimReviewBundle findings → ReviewerFinding list + ReviewerSummary.
- Add adapter conversion tests.
- Load media_quality_report.json.
- Implement FinalVideoReviewer.
- Handle missing media quality report as warning.
- Add FinalVideoReviewer tests.
```

Verification：

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/test_paper_fidelity_final_reviewer_adapter.py tests/test_final_video_reviewer.py -v
```

---

### Day 3：VisualAlignmentReviewer and Subtitle final reviewer

```text
- Load asset_plan / media metadata / figures.json.
- Implement deterministic visual alignment checks.
- Reuse subtitle readability results from media_quality_report.
- Add tests.
```

Verification：

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/test_visual_alignment_reviewer.py -v
```

---

### Day 4：DevilAdvocate and style final checks

```text
- Implement deterministic hype / forbidden phrase checks.
- Implement prompt-injection pattern detection.
- Integrate style forbidden phrases if available.
- Add tests.
```

Verification：

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/test_devil_advocate_reviewer.py tests/test_reviewer_prompt_injection_guards.py -v
```

---

### Day 5：FinalArbiter

```text
- Aggregate reviewer summaries.
- Produce FinalGateDecision.
- Add gate status semantics.
- Add tests.
```

Verification：

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/test_final_arbiter.py -v
```

---

### Day 6：Pipeline / CLI integration

```text
- Add final_review stage.
- Wire final_review_service into pipeline.
- Update project_state stage status.
- Add pipeline tests.
```

Verification：

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/test_mvp3_final_review_pipeline.py -v
```

---

### Day 7：Manual smoke and status

```text
- Run final_review on mvp2c_thin_smoke.
- Write MVP3_FINAL_REVIEW_SMOKE.md.
- Run full regression.
- Create MVP3_STATUS.md.
```

Verification：

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/ -v
```

---

## 12. Status template

MVP3 must create `MVP3_STATUS.md` using the standard v8.2 status structure：

```markdown
# MVP3 Status

Last updated: YYYY-MM-DD

## Contract complete
- Completed artifact / schema / CLI / service contract

## Current verification
- Focused tests
- Full regression
- Manual smoke

## Known quality gaps
- Remaining reviewer / gate / calibration gaps

## Hardening backlog
- Items deferred to HARDEN-4 / MVP4 / MVP2C-full

## Recommended next step
- Recommended next sprint or explicit route decision
```

---

## 13. Acceptance criteria

MVP3 is accepted only if all are true：

```text
[ ] Final review schemas exist and pass roundtrip tests.
[ ] `final_review` stage exists.
[ ] `final_review` requires composition == done.
[ ] MVP3 reads active scene source and does not hardcode scenes.json.
[ ] FinalReviewBundle is produced.
[ ] FinalGateDecision is produced.
[ ] Review outputs use revision numbering and do not overwrite prior reviews.
[ ] FinalVideoReviewer reads media_quality_report.json when available.
[ ] VisualAlignmentReviewer checks asset/media consistency.
[ ] DevilAdvocate catches hype and prompt-injection patterns.
[ ] FinalArbiter maps reviewer results to pass / human_check / reject.
[ ] Warnings can pass gate.
[ ] Blocking high/critical findings do not pass silently.
[ ] project_state.stages.final_review is updated correctly.
[ ] No auto-fix / auto-regeneration is introduced.
[ ] No Streamlit UI is introduced.
[ ] Full pytest regression passes.
[ ] Manual smoke on mvp2c_thin_smoke or equivalent passes.
[ ] MVP3_STATUS.md is created using the standard template.
```

---

## 14. Post-MVP3 handoff

After MVP3 acceptance, do not automatically proceed to any one route.

Use MVP3 results to choose among：

```text
Option A: HARDEN-4 reviewer calibration
  Choose this if:
  - reviewer gates exist
  - next risk is false positive / false negative calibration
  - we need golden dataset / prompt injection / arbiter stability before research use

Option B: MVP4 inspection UI prototype
  Choose this if:
  - final review reports exist
  - manual navigation across claims / scenes / media / reviews is painful
  - user needs an interface to inspect and decide human_check cases

Option C: MVP2C-full media generation
  Choose this if:
  - reviewer gate and media quality gate are stable
  - priority shifts back to richer visuals / VRM / AI image generation
```

Recommended default after MVP3：

```text
HARDEN-4 reviewer calibration
```

Reason：

```text
MVP3 creates reviewer gates. Before relying on them for research or publication decisions,
the gates should be calibrated against golden cases to reduce false negatives.
```

---

## 15. Final instruction to coding agent

Implement MVP3 as a structured reviewer committee and final review gate.

Hard constraints：

```text
- Read active scene source; do not hardcode scenes.json.
- Do not auto-rewrite or auto-regenerate artifacts.
- Do not introduce UI.
- Do not introduce ComfyUI / VRM / Playwright.
- Preserve existing artifacts.
- Write revision-numbered review outputs.
- Produce FinalReviewBundle and FinalGateDecision.
- Update project_state final_review stage.
- Keep all outputs schema-validated and test-covered.
```

Expected major artifacts：

```text
runs/{project_id}/reviews/final_review_rev001.json
runs/{project_id}/reviews/final_gate_decision_rev001.json
docs/sprints/MVP3/MVP3_STATUS.md
docs/sprints/MVP3/reports/MVP3_FINAL_REVIEW_SMOKE.md
```
