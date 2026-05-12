# IMPLEMENTATION PLAN — P2S HARDEN-3：Media Quality / Composition

> 文件定位：本文件是 **HARDEN-3 sprint contract**，可直接交給 coding agent / Codex / Claude Code 作為開工依據。  
> 本階段不是 full MVP2C，也不是導入 ComfyUI / VRM / AI image generation。  
> **HARDEN-3 的目標是補強 MVP2C-thin 產生的最小影片在媒體品質、時間對齊、字幕可讀性、composition 穩定性、fallback 可見性上的缺口。**

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
```

MVP2C-thin 已完成：

```text
asset_plan.json
→ audio/*.wav
→ assets/*.png
→ segments/*.mp4
→ final/output.mp4
```

MVP2C-thin status 顯示：

```text
Focused MVP2C-thin tests passed
Full regression: 179 passed
Fake-backend CLI smoke passed
final/output.mp4 produced
```

但目前仍有以下已知 gaps：

```text
- Visuals are deterministic placeholders, not polished media.
- Diagram, metaphor, and chart prompts fall back to text cards.
- Paper figures require extracted image paths; caption-only figures fall back to text cards.
- Real Edge-TTS smoke is conditionally accepted pending network availability.
- Media quality, timing, subtitle readability, composition, loudness, MP4 compatibility, and fallback quality reporting remain to be hardened.
```

因此依照 Architecture Spec v8.2 的治理節奏，下一步是：

```text
HARDEN-3: Media Quality / Composition
```

---

## 1. HARDEN-3 核心目標

HARDEN-3 的目標是把 MVP2C-thin 的「可播放」提升到「可檢查、可診斷、可穩定重跑」的媒體基線。

本 sprint 要補強七件事：

```text
1. TTS timing and duration consistency
2. Subtitle readability
3. Text-card / figure-card layout quality
4. Segment composition stability
5. Audio loudness and silence handling
6. Final MP4 compatibility
7. Fallback quality reporting
```

完成後，系統不一定要產生漂亮影片，但必須能清楚回答：

```text
- 每段 audio duration 是否正常？
- subtitle 是否過長、過小或超出安全區？
- text card / figure card 是否可讀？
- segment 是否能被 ffprobe 讀取？
- final MP4 是否能在常見播放器/平台規格下播放？
- audio loudness 是否過小或過大？
- 哪些 scene 使用 fallback？fallback 對品質造成什麼影響？
```

---

## 2. Non-goals：HARDEN-3 明確不做

HARDEN-3 不是 full media generation。

禁止在本 sprint 中實作：

```text
- ComfyUI / RunningHub image generation
- Stable Diffusion / Flux / local image model calls
- VRM rendering
- lip sync / motion generation
- Playwright template system
- complex animation
- BGM selection UI
- full Streamlit UI
- full reviewer committee
- auto-fix loop
- publishing/export workflow
```

允許實作：

```text
- media quality validators
- duration / ffprobe helpers
- subtitle readability checks
- text-card / figure-card layout improvements
- audio loudness measurement / optional normalization
- final MP4 compatibility checks
- fallback quality report
- real Edge-TTS smoke when network is available
```

---

## 3. 設計原則

### 3.1 Harden the thin pipeline, do not expand scope

HARDEN-3 的任務是讓 MVP2C-thin 更可靠，而不是把它擴張成 MVP2C-full。

```text
Correct:
  Improve text-card readability.
  Validate segment duration.
  Add loudness report.
  Add MP4 compatibility checks.

Incorrect:
  Add AI image generation.
  Add VRM character rendering.
  Add lip sync.
  Add complex HTML template engine.
```

### 3.2 Quality report first

HARDEN-3 的第一優先不是自動修正，而是讓品質問題可見化。

```text
media_quality_report.json
→ tells us what is wrong
→ later MVPs / hardening passes can decide how to fix
```

### 3.3 Deterministic checks over subjective aesthetics

本階段不評估「好不好看」，只評估可操作的媒體品質：

```text
- duration readable
- audio exists and is non-empty
- segment exists and is playable
- subtitle fits safe area
- text size above threshold
- loudness within target range
- fallback rate visible
```

---

## 4. 新增 / 修改檔案清單

### 4.1 Models

新增或擴充：

```text
p2s_core/models/media_quality.py
```

建議新增 schema：

```text
AudioQualityResult
SubtitleReadabilityResult
VisualLayoutQualityResult
SegmentQualityResult
CompositionQualityResult
FallbackQualityReport
MediaQualityReport
```

### 4.2 Services

新增或擴充：

```text
p2s_core/services/media_quality.py
p2s_core/services/audio_quality.py
p2s_core/services/subtitle_quality.py
p2s_core/services/visual_layout_quality.py
p2s_core/services/ffprobe_utils.py
p2s_core/services/loudness.py
```

若目前已有 `video_service.py` / `segment_composer.py`，HARDEN-3 可在現有服務旁新增 validator helper，不要把 validation 邏輯混進 generation 主流程太深。

### 4.3 Pipeline / CLI

新增或擴充 stage：

```text
media_quality_check
```

或若不想新增正式 stage，至少提供：

```bash
python -m p2s_core.cli run --stage media_quality_check --project <project_id>
```

建議將 HARDEN-3 的檢查獨立為 stage，原因：

```text
- 不必每次重新生成 audio / segments 才能重新檢查。
- 可以在 MVP2C-thin outputs 上反覆跑。
- 方便未來 UI 顯示 media quality dashboard。
```

Stage dependency：

```text
media_quality_check requires composition == done
```

輸出：

```text
runs/{project_id}/media_quality_report.json
```

### 4.4 Tests

新增：

```text
tests/test_media_quality_schema.py
tests/test_audio_quality.py
tests/test_subtitle_quality.py
tests/test_visual_layout_quality.py
tests/test_segment_quality.py
tests/test_composition_quality.py
tests/test_fallback_quality_report.py
tests/test_harden3_pipeline.py
```

### 4.5 Docs

新增：

```text
docs/sprints/HARDEN3/IMPLEMENTATION_PLAN_HARDEN3_MEDIA_QUALITY.md
docs/sprints/HARDEN3/HARDEN3_STATUS.md
docs/sprints/HARDEN3/reports/HARDEN3_MEDIA_QUALITY_SMOKE.md
```

---

## 5. Schema 設計

### 5.1 AudioQualityResult

```python
class AudioQualityResult(BaseModel):
    scene_id: str
    audio_path: str
    exists: bool
    file_size_bytes: int | None = None
    duration_sec: float | None = None
    loudness_lufs: float | None = None
    peak_dbfs: float | None = None
    silence_ratio: float | None = None
    pass_gate: bool
    warnings: list[str] = []
```

最低檢查：

```text
- audio file exists
- file size > 0
- duration readable
- duration_sec > 0.3
- optional: loudness_lufs within configured target range
```

---

### 5.2 SubtitleReadabilityResult

```python
class SubtitleReadabilityResult(BaseModel):
    scene_id: str
    subtitle_text: str
    char_count: int
    estimated_lines: int
    font_size: int | None = None
    safe_area_ok: bool = True
    too_long: bool = False
    pass_gate: bool
    warnings: list[str] = []
```

初版 deterministic rules：

```text
- subtitle_text empty → warning
- zh-TW subtitle char_count > 28 → warning（too_long = True）
- estimated_lines > 2 → warning
- estimated_lines > 3 → safe_area_ok = False（超出任何合理字幕框，hard fail）
- char_count > 50 → safe_area_ok = False（極端長度，hard fail）
```

`safe_area_ok = False` 的觸發條件基於字數 / 估算行數，不依賴實際 pixel rendering。
若 MVP2C-thin visual service 在 render 時有計算 safe area，可直接從 render result 回傳；
若沒有，則由 subtitle quality helper 依上述 deterministic rules 計算。

不要在 HARDEN-3 做 LLM subtitle rewrite。只報告問題。

---

### 5.3 VisualLayoutQualityResult

```python
class VisualLayoutQualityResult(BaseModel):
    scene_id: str
    visual_path: str
    width: int | None = None
    height: int | None = None
    layout_type: str | None = None
    text_bbox: list[int] | None = None
    figure_bbox: list[int] | None = None
    safe_area_ok: bool = True
    min_text_size_ok: bool = True
    figure_size_ratio: float | None = None
    pass_gate: bool
    warnings: list[str] = []
```

初版 checks：

```text
- PNG exists and can be opened.
- resolution matches expected render resolution.
- text bbox stays within safe area.
- figure card: figure_size_ratio not too small.
- text card: primary text not empty.
```

---

### 5.4 SegmentQualityResult

```python
class SegmentQualityResult(BaseModel):
    scene_id: str
    segment_path: str
    exists: bool
    file_size_bytes: int | None = None
    duration_sec: float | None = None
    audio_duration_sec: float | None = None
    duration_delta_sec: float | None = None
    ffprobe_readable: bool = False
    pass_gate: bool
    warnings: list[str] = []
```

初版 checks：

```text
- segment exists
- file size > 0
- ffprobe can read duration if available
- abs(segment_duration - audio_duration) <= tolerance
  初版 tolerance = 0.5 秒
  超過 1.0 秒 → duration_delta warning 升級為 fail candidate（仍為 warning，但 blocking_issues 記錄）
```

若 ffprobe 不可用：

```text
warning only, unless segment file missing or empty
```

---

### 5.5 CompositionQualityResult

```python
class CompositionQualityResult(BaseModel):
    project_id: str
    output_path: str
    exists: bool
    file_size_bytes: int | None = None
    duration_sec: float | None = None
    expected_duration_sec: float | None = None
    duration_delta_sec: float | None = None
    ffprobe_readable: bool = False
    codec_video: str | None = None
    codec_audio: str | None = None
    pixel_format: str | None = None
    pass_gate: bool
    warnings: list[str] = []
```

初版 checks：

```text
- final/output.mp4 exists
- file size > 0
- duration roughly equals sum(segment durations)
- video codec preferably h264 / libx264 output
- pixel format preferably yuv420p
- audio codec preferably aac
```

---

### 5.6 FallbackQualityReport

```python
class FallbackQualityReport(BaseModel):
    scene_count: int
    fallback_visual_count: int
    fallback_ratio: float
    fallback_by_reason: dict[str, int] = {}
    scenes_using_fallback: list[str] = []
    quality_level: Literal["good", "acceptable", "degraded", "minimal"]
    warnings: list[str] = []
```

`fallback_by_reason` key 定義：

```text
key 來源：asset_plan 中各 scene 的 visual_plan.asset_source 及 fallback 原因。
預定義 key（snake_case）：
  "no_figure_metadata"       ← paper_figure 但找不到 figures.json
  "caption_only_figure"      ← figure 有 caption 但無 image_path
  "diagram_prompt_fallback"  ← diagram_prompt 退為 text_card
  "metaphor_image_fallback"  ← metaphor_image_prompt 退為 text_card
  "chart_prompt_fallback"    ← chart_prompt 退為 text_card
  "unknown_fallback"         ← 其他無法分類的 fallback 原因

若未來出現新的 fallback 原因，統一用 snake_case 並加入此清單。
```

Quality level rules:

```text
good:
  fallback_ratio == 0

acceptable:
  fallback_ratio <= 0.3

degraded:
  fallback_ratio <= 0.7

minimal:
  fallback_ratio > 0.7
```

This is not a fail gate by default. It is a visibility mechanism.

---

### 5.7 MediaQualityReport

```python
class MediaQualityReport(BaseModel):
    project_id: str
    audio_results: list[AudioQualityResult]
    subtitle_results: list[SubtitleReadabilityResult]
    visual_layout_results: list[VisualLayoutQualityResult]
    segment_results: list[SegmentQualityResult]
    composition_result: CompositionQualityResult
    fallback_quality: FallbackQualityReport
    pass_gate: bool
    blocking_issues: list[str] = []
    warnings: list[str] = []
    created_at: str
```

輸出：

```text
runs/{project_id}/media_quality_report.json
```

---

## 6. Validation / quality gates

### 6.1 Hard fail

```text
- final/output.mp4 missing
- final/output.mp4 file size == 0
- any required audio file missing
- any required segment file missing
- visual PNG missing for any scene
- schema validation failure
- composition duration cannot be determined when ffprobe is available and readable segments exist
```

### 6.2 Warning only

```text
- ffprobe unavailable
- loudness unavailable
- subtitle too long
- fallback visual used
- diagram/metaphor/chart fallback to text card
- caption-only figure fallback to text card
- figure card ratio too small but still readable
- final MP4 codec metadata unavailable
```

### 6.3 Pass gate logic

```text
pass_gate = true if:
- no hard fail
- final/output.mp4 exists and non-empty
- every scene has audio, visual, segment artifact
- composition result passes basic checks

pass_gate = false if:
- any hard fail
```

HARDEN-3 不因 fallback ratio high 自動 fail，但要在 `fallback_quality.quality_level` 清楚標示。

---

## 7. Execution rules

### 7.1 Input artifacts

Required:

```text
runs/{project_id}/asset_plan.json
runs/{project_id}/media_generation_report.json
runs/{project_id}/media_metadata/audio.json
runs/{project_id}/media_metadata/visuals.json
runs/{project_id}/media_metadata/segments.json
runs/{project_id}/media_metadata/composition.json
runs/{project_id}/final/output.mp4
```

Optional:

```text
runs/{project_id}/final/output_subtitles.srt
runs/{project_id}/figures.json
runs/{project_id}/extraction_quality_report.json
```

### 7.2 Report-only first

HARDEN-3 should first implement report-only behavior:

```text
Read existing MVP2C-thin outputs
→ validate
→ write media_quality_report.json
```

No regeneration in the first version.

### 7.3 No automatic rewrite

HARDEN-3 must not automatically rewrite subtitles, regenerate text cards, normalize audio, or recompose video unless explicitly added in a later pass.

Allowed:

```text
- report issue
- mark warning
- mark pass/fail
```

Not allowed in first pass:

```text
- auto-rewrite subtitle
- auto-resize layout
- auto-normalize loudness
- auto-recompose final MP4
```

---

## 8. Tests

### 8.1 Schema tests

File:

```text
tests/test_media_quality_schema.py
```

Must test:

```text
- AudioQualityResult roundtrip
- SubtitleReadabilityResult roundtrip
- VisualLayoutQualityResult roundtrip
- SegmentQualityResult roundtrip
- CompositionQualityResult roundtrip
- FallbackQualityReport roundtrip
- MediaQualityReport roundtrip
```

---

### 8.2 Audio quality tests

File:

```text
tests/test_audio_quality.py
```

Must test:

```text
- valid wav passes
- missing audio fails
- empty audio fails
- duration readable
- ffprobe/unavailable loudness path warns, not fails
```

---

### 8.3 Subtitle quality tests

File:

```text
tests/test_subtitle_quality.py
```

Must test:

```text
- short subtitle passes
- empty subtitle warns
- long subtitle warns
- estimated 3-line subtitle warns
```

---

### 8.4 Visual layout quality tests

File:

```text
tests/test_visual_layout_quality.py
```

Must test:

```text
- valid PNG passes
- missing PNG fails
- unreadable PNG fails
- resolution mismatch warns（not fail；與 Section 6.2 一致）
- text card with empty text warns
- figure card with tiny figure warns
```

---

### 8.5 Segment quality tests

File:

```text
tests/test_segment_quality.py
```

Must test:

```text
- existing segment passes basic file checks
- missing segment fails
- empty segment fails
- duration delta warning when ffprobe available
- ffprobe unavailable warning path
```

---

### 8.6 Composition quality tests

File:

```text
tests/test_composition_quality.py
```

Must test:

```text
- final/output.mp4 exists and non-empty
- missing final video fails
- empty final video fails
- codec metadata check when ffprobe available
- ffprobe unavailable warning path
```

---

### 8.7 Fallback report tests

File:

```text
tests/test_fallback_quality_report.py
```

Must test:

```text
- fallback_ratio 0 → good
- fallback_ratio <= 0.3 → acceptable
- fallback_ratio <= 0.7 → degraded
- fallback_ratio > 0.7 → minimal
- fallback reasons counted
```

---

### 8.8 Pipeline tests

File:

```text
tests/test_harden3_pipeline.py
```

Must test:

```text
- run --stage media_quality_check writes media_quality_report.json
- media_quality_check requires composition == done
- project_state records media_quality_check status
- report pass_gate true on valid fake-backend smoke project
- report pass_gate false when final/output.mp4 missing
```

---

## 9. Manual smoke plan

Use an MVP2C-thin accepted project:

```bash
.\.venv-win\Scripts\python.exe -m p2s_core.cli status --project mvp2c_thin_smoke
.\.venv-win\Scripts\python.exe -m p2s_core.cli run --stage media_quality_check --project mvp2c_thin_smoke
```

Expected output:

```text
runs/mvp2c_thin_smoke/media_quality_report.json
```

Expected report:

```text
pass_gate: true
composition_result.exists: true
composition_result.file_size_bytes > 0
fallback_quality.quality_level: acceptable/degraded/minimal depending fixture
```

Manual inspection:

```text
- Open final/output.mp4.
- Confirm it plays.
- Confirm scene order is correct.
- Confirm text cards are at least readable.
- Record any visual/audio issue in HARDEN3_STATUS.md Known quality gaps.
```

---

## 10. Day-by-day sprint plan

### Day 1：Schemas and report contract

```text
- Add media quality schemas.
- Add exports.
- Add roundtrip tests.
- Define media_quality_report.json output path.
```

Verification:

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/test_media_quality_schema.py -v
```

---

### Day 2：Audio / subtitle quality checks

```text
- Add audio quality helper.
- Add subtitle readability helper.
- Add tests.
```

Verification:

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/test_audio_quality.py tests/test_subtitle_quality.py -v
```

---

### Day 3：Visual layout / fallback quality

```text
- Add PNG readability and layout checks.
- Add fallback quality report.
- Add tests.
```

Verification:

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/test_visual_layout_quality.py tests/test_fallback_quality_report.py -v
```

---

### Day 4：Segment / composition quality

```text
- Add segment quality checks.
- Add composition quality checks.
- Add ffprobe utility wrapper.
- Add tests.
```

Verification:

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/test_segment_quality.py tests/test_composition_quality.py -v
```

---

### Day 5：Pipeline / CLI integration

```text
- Add media_quality_check stage.
- Add CLI support.
- Update project_state stage status.
- Add pipeline tests.
```

Verification:

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/test_harden3_pipeline.py -v
```

---

### Day 6：Manual smoke and report

```text
- Run media_quality_check on mvp2c_thin_smoke.
- Inspect final/output.mp4 manually.
- Write HARDEN3_MEDIA_QUALITY_SMOKE.md.
```

---

### Day 7：Status and full regression

```text
- Run full regression.
- Create HARDEN3_STATUS.md.
- Decide post-HARDEN-3 route:
  Option A: MVP2C-full media generation
  Option B: MVP3 reviewer committee
  Option C: MVP4 inspection UI prototype
```

Verification:

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/ -v
```

---

## 11. Status template

HARDEN-3 must create `HARDEN3_STATUS.md` using the standard v8.2 status structure:

```markdown
# HARDEN-3 Status

Last updated: YYYY-MM-DD

## Contract complete
- Completed artifact / schema / CLI / service contract

## Current verification
- Focused tests
- Full regression
- Manual smoke

## Known quality gaps
- Remaining media quality / layout / audio / composition gaps

## Hardening backlog
- Items deferred to MVP2C-full / MVP3 / MVP4

## Recommended next step
- Decide one of:
  - MVP2C-full media generation
  - MVP3 reviewer committee
  - MVP4 inspection UI prototype
```

---

## 12. Acceptance criteria

HARDEN-3 is accepted only if all are true:

```text
[ ] Media quality schemas exist and pass roundtrip tests.
[ ] media_quality_check stage exists or equivalent runner exists.
[ ] media_quality_check requires composition == done.
[ ] media_quality_report.json is produced.
[ ] Audio quality checks cover exists / non-empty / duration.
[ ] Subtitle readability checks cover empty / long / estimated multi-line cases.
[ ] Visual layout checks cover PNG readable / missing / resolution / text / figure size.
[ ] Segment checks cover exists / non-empty / duration when ffprobe available.
[ ] Composition checks cover final/output.mp4 exists / non-empty / duration / codec metadata where available.
[ ] FallbackQualityReport is produced and classifies fallback quality level.
[ ] Missing final/output.mp4 fails the gate.
[ ] Valid MVP2C-thin fake-backend smoke project passes the gate.
[ ] No ComfyUI / VRM / Playwright / AI image generation is introduced.
[ ] No auto-rewrite / auto-regeneration is introduced in first pass.
[ ] Full pytest regression passes.
[ ] Manual smoke on mvp2c_thin_smoke or equivalent passes.
[ ] HARDEN3_STATUS.md is created using the standard template.
[ ] Recommended next step is explicitly chosen or explicitly deferred.
```

---

## 13. Post-HARDEN-3 handoff

After HARDEN-3 acceptance, do not automatically proceed to full media generation.

Use the HARDEN-3 results to decide:

```text
Option A: MVP2C-full media generation
  Choose this if:
  - media pipeline is stable
  - text-card / figure-card quality is acceptable
  - main missing value is richer visuals / VRM / AI image generation

Option B: MVP3 reviewer committee
  Choose this if:
  - media pipeline works
  - main risk is factuality / visual alignment / final video review
  - research direction needs stronger review/evaluation layer

Option C: MVP4 inspection UI prototype
  Choose this if:
  - pipeline works but manual inspection/editing is painful
  - project needs UI to manage claims / scenes / reviews / media artifacts
```

---

## 14. Final instruction to coding agent

Implement HARDEN-3 as a report-first media quality hardening sprint.

Hard constraints:

```text
- Do not implement full media generation.
- Do not introduce ComfyUI / VRM / Playwright.
- Do not auto-regenerate media in first pass.
- Read existing MVP2C-thin artifacts.
- Produce media_quality_report.json.
- Make fallback quality visible.
- Validate final/output.mp4.
- Preserve prior stage statuses during migration.
- Keep all outputs schema-validated and test-covered.
```

Expected major artifacts:

```text
runs/{project_id}/media_quality_report.json
docs/sprints/HARDEN3/HARDEN3_STATUS.md
docs/sprints/HARDEN3/reports/HARDEN3_MEDIA_QUALITY_SMOKE.md
```
