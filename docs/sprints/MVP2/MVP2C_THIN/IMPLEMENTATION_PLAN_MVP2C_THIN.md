# IMPLEMENTATION PLAN — P2S MVP2C-thin：Minimal Playable Video Pipeline

> 文件定位：本文件是 **MVP2C-thin sprint contract**，可直接交給 coding agent / Codex / Claude Code 作為開工依據。  
> 本階段目標是從 `asset_plan.json` 產生第一支 **最小可播放影片**。  
> **MVP2C-thin 只建立 audio / visual placeholder / segment / final MP4 的最小閉環，不做 full media generation。**

---

## 0. 當前前提

目前 P2S 已完成：

```text
MVP0     → schema / state / CLI / basic extraction
MVP1     → claim extraction / evidence mapping / deterministic reviewers
MVP2A    → narrative planning / presentation planning
MVP2A-2  → LLM quality rewrite / active_scene_source
MVP2B    → asset_preparation / asset_plan.json
HARDEN-1 → extraction / evidence / figure metadata hardening
```

目前可用的主要上游 artifact：

```text
runs/{project_id}/asset_plan.json
runs/{project_id}/figures.json
runs/{project_id}/extraction_quality_report.json
runs/{project_id}/project_state.json
```

HARDEN-1 已修正並驗證：

```text
- section detection 使用 raw text 做 heading/boundary detection，section body 再 normalization
- figure metadata baseline 可產生 figures.json
- smoke set: 3 papers passed
- full regression: 162 passed
```

因此可以進入：

```text
MVP2C-thin: Minimal playable video pipeline
```

---

## 1. MVP2C-thin 核心目標

MVP2C-thin 的目標是建立最小可播放影片閉環：

```text
asset_plan.json
→ audio/*.wav
→ assets/*.png
→ segments/*.mp4
→ final/output.mp4
```

它要驗證：

```text
1. `asset_plan.json` 是否足以驅動實際產出。
2. 每個 scene 是否能生成 audio。
3. 每個 scene 是否能產生最小 visual placeholder。
4. 每個 scene 是否能合成 segment。
5. segments 是否能 concat 成 final/output.mp4。
6. project_state 是否能記錄 asset_generation / composition 的 stage 狀態。
```

MVP2C-thin 的完成標誌：

```text
runs/{project_id}/audio/{scene_id}.wav exists
runs/{project_id}/assets/{scene_id}_*.png exists
runs/{project_id}/segments/{scene_id}.mp4 exists
runs/{project_id}/final/output.mp4 exists
project_state.stages.asset_generation.status == "done"
project_state.stages.composition.status == "done"
```

---

## 2. Non-goals：MVP2C-thin 明確不做

MVP2C-thin 不是 full media generation，不追求畫面品質。

禁止在本 sprint 中實作：

```text
- ComfyUI / RunningHub image generation
- Stable Diffusion / Flux / local image model calls
- VRM rendering
- lip sync
- motion generation
- complex HTML template system
- Playwright rendering
- full visual reviewer loop
- auto-fix loop
- Streamlit UI
- BGM selection UI
- publication/export workflow
- persona acquisition
```

允許實作：

```text
- Edge-TTS real audio generation
- simple text-card PNG rendering
- static clean background PNG rendering
- use selected paper figure when available
- ffmpeg image+audio → segment MP4
- ffmpeg concat segments → final MP4
- minimal subtitles baked into text-card image or generated as .srt
- deterministic media metadata recording
```

---

## 3. 設計原則

### 3.1 Thin means stable, not beautiful

MVP2C-thin 的核心是「穩定產出可播放影片」，不是「漂亮」。

可接受：

```text
- 背景很簡單
- 只有 text card
- 圖表顯示方式很保守
- 字幕樣式樸素
- 沒有角色動畫
- 沒有 AI 生圖
```

不可接受：

```text
- asset_plan.json 有些 scene 無法執行
- audio / segment path 不穩定
- ffmpeg command 難以重現
- 一個 scene 失敗就沒有清楚錯誤
- project_state 沒記錄 stage 狀態
- 偷接 ComfyUI / VRM / Playwright 導致 sprint 膨脹
```

### 3.2 AssetPlan is the execution contract

MVP2C-thin 必須以 `asset_plan.json` 為唯一主要執行計畫。

不應從 `scenes.json` 或 `presentation_plan.json` 重新推斷 scene 策略。

```text
MVP2B 決定：每幕需要什麼資產。
MVP2C-thin 執行：照 asset_plan 產出最小資產與影片。
```

### 3.3 TTS-driven duration

每個 scene 應先產生 TTS audio，取得實際 audio duration，再用 audio duration 產生 segment。

```text
TTS audio duration
→ segment duration
→ final concat timing
```

若 audio duration 無法讀取，才 fallback 到 `asset_plan.tts_plan.estimated_duration_sec`。

### 3.4 Fallback must always produce something playable

每個 scene 必須盡力產出 segment。若指定 paper figure 不可用，應 fallback 到 text card 或 static background。

MVP2C-thin 不因單一 visual source 不存在而整體失敗，除非連 text card/static background 也無法產生。

---

## 4. 新增 / 修改檔案清單

### 4.1 Services

新增或實作：

```text
p2s_core/services/tts_service.py
p2s_core/services/visual_placeholder.py
p2s_core/services/segment_composer.py
p2s_core/services/video_service.py
p2s_core/services/media_metadata.py
```

若既有檔案已存在，則在現有檔案內補 MVP2C-thin 最小功能。

### 4.2 Models

新增或擴充：

```text
p2s_core/models/media.py
```

建議新增 schema：

```text
GeneratedAudio
GeneratedVisual
GeneratedSegment
CompositionResult
MediaGenerationReport
```

### 4.3 Pipeline / CLI

修改：

```text
p2s_core/pipelines/paper_summary.py
p2s_core/cli.py
p2s_core/models/project_state.py
```

目標：

```text
- 支援 `run --stage asset_generation`
- 支援 `run --stage composition`
- status 顯示 asset_generation / composition
- migration 不重設已完成 stages
```

### 4.4 Tests

新增：

```text
tests/test_media_schema.py
tests/test_tts_service_thin.py
tests/test_visual_placeholder.py
tests/test_segment_composer.py
tests/test_video_service_thin.py
tests/test_mvp2c_thin_pipeline.py
```

### 4.5 Docs

新增：

```text
docs/sprints/MVP2/MVP2C_THIN/IMPLEMENTATION_PLAN_MVP2C_THIN.md
docs/sprints/MVP2/MVP2C_THIN/MVP2C_THIN_STATUS.md
```

---

## 5. Schema 設計

### 5.1 GeneratedAudio

```python
class GeneratedAudio(BaseModel):
    scene_id: str
    text: str
    backend: str
    voice: str | None = None
    speed: float = 1.0
    output_path: str
    duration_sec: float | None = None
    placeholder: bool = False
    generation_status: Literal["done", "failed", "fallback"] = "done"
    warnings: list[str] = []
    created_at: str
```

要求：

```text
- text 必須等於 asset_plan.tts_plan.text。
- output_path 應為 audio/{scene_id}.wav。
- duration_sec 優先由實際音檔讀取。
```

---

### 5.2 GeneratedVisual

```python
class GeneratedVisual(BaseModel):
    scene_id: str
    asset_source: str
    output_path: str
    source_path: str | None = None
    fallback_level: str | None = None
    width: int = 1080
    height: int = 1920
    generation_status: Literal["done", "failed", "fallback"] = "done"
    warnings: list[str] = []
    created_at: str
```

`asset_source` 對應 `VisualAssetPlan.asset_source`。

MVP2C-thin 支援的 resolved behavior：

```text
asset_source == "paper_figure"          → use paper figure if image_path exists; otherwise text_card fallback
asset_source == "diagram_prompt"        → text_card fallback, do not generate diagram image
asset_source == "metaphor_image_prompt" → text_card fallback, do not generate AI image
asset_source == "chart_prompt"          → text_card fallback, do not invent chart data
asset_source == "text_card"             → render text card
asset_source == "static_background"     → render static background with subtitle
asset_source == "none"                  → render static background with subtitle
```

---

### 5.3 GeneratedSegment

```python
class GeneratedSegment(BaseModel):
    scene_id: str
    audio_path: str
    visual_path: str
    output_path: str
    duration_sec: float | None = None
    ffmpeg_command: list[str] = []
    generation_status: Literal["done", "failed"] = "done"
    warnings: list[str] = []
    created_at: str
```

---

### 5.4 CompositionResult

```python
class CompositionResult(BaseModel):
    project_id: str
    segment_paths: list[str]
    output_path: str
    subtitle_path: str | None = None
    duration_sec: float | None = None
    ffmpeg_command: list[str] = []
    generation_status: Literal["done", "failed"] = "done"
    warnings: list[str] = []
    created_at: str
```

---

### 5.5 MediaGenerationReport

```python
class MediaGenerationReport(BaseModel):
    project_id: str
    scene_count: int
    audio_count: int
    visual_count: int
    segment_count: int
    fallback_visual_count: int
    failed_scene_count: int
    final_video_path: str | None = None
    warnings: list[str] = []
    created_at: str
```

輸出：

```text
runs/{project_id}/media_generation_report.json
```

---

## 6. Execution rules

### 6.1 Input resolution

MVP2C-thin 必須讀取：

```text
runs/{project_id}/asset_plan.json
```

可選讀取：

```text
runs/{project_id}/figures.json
runs/{project_id}/extraction_quality_report.json
```

若 `asset_plan.json` 不存在：

```text
stage failed
```

若 `figures.json` 不存在：

```text
warning only；paper_figure scenes fallback to text_card
```

---

### 6.2 TTS generation rules

每個 `SceneAssetPlan` 都產生 audio。

```text
audio output path: audio/{scene_id}.wav
backend: Edge-TTS for MVP2C-thin
```

Voice 選擇優先序：

```text
1. asset_plan.tts_plan.voice
2. persona voice profile default voice
3. config.tts.default_voice
4. fallback: zh-TW-HsiaoChenNeural
```

Speed：

```text
使用 asset_plan.tts_plan.speed。
若 Edge-TTS 需要字串格式，service 內部轉換。
```

Failure policy：

```text
- 單一 TTS failed → retry 1-2 次。
- 仍 failed → asset_generation stage failed（整體中止）。
```

理由：沒有 audio 的 scene 無法合成 segment，composition 也必然失敗。早 fail 比在 composition 階段才發現缺少 segment 清楚。

MVP2C-thin 不使用 fake beep audio 作為正式 fallback，避免產出看似成功但不可用的 final video。

> **`failed_scene_count` 欄位語義說明**：
> `MediaGenerationReport.failed_scene_count` 記錄的是 visual 或 segment 合成失敗的 scene 數量，
> 不包含 TTS failed（TTS failed 直接觸發 stage failed，不進入 report）。
> 此欄位設計供未來允許 partial fallback 的版本使用；MVP2C-thin 中若 > 0 則 stage failed。

---

### 6.3 Visual placeholder rules

所有 scene 都必須產生 PNG，解析度依以下優先序決定：

```text
resolution 讀取優先序：
1. asset_plan.plans[n].render_plan.resolution（若存在且格式合法，例如 "1080x1920"）
2. 預設 1080x1920（portrait）

GeneratedVisual.width / height 以最終 resolved 值記錄，不使用 schema default。
所有 PNG 輸出必須使用 resolved resolution，不可 hardcode。
```

支援三種最小 visual：

```text
1. paper figure canvas
2. text card
3. static clean background with subtitle
```

#### Case A: paper_figure

若 `selected_figure_ids` 對應到 `figures.json`，且該 figure 有 `image_path`：

```text
- 將 figure 放在 clean canvas 中央。
- 顯示 subtitle 或 short title。
- 不拉伸破壞比例。
```

若 figure 只有 caption metadata、沒有 image_path：

```text
- fallback to text_card。
- warnings += caption_without_image fallback。
```

若找不到 figure：

```text
- fallback to text_card。
- warnings += paper figure missing fallback。
```

#### Case B: text_card

```text
- 使用 subtitle_text 作為主文字。
- 若 subtitle_text 太短或為空，使用 asset_plan.tts_plan.text 的前半句。
- 不得讀取 scenes.json 的 voice_text；tts_plan.text 是已保證等效的合約來源。
- 背景 static clean。
```

#### Case C: static_background / none

```text
- 產生乾淨背景。
- 放置 subtitle_text。
```

#### Case D: diagram_prompt / metaphor_image_prompt / chart_prompt

MVP2C-thin 不生成 AI image 或 chart。

```text
- fallback to text_card。
- warnings += unsupported visual source in thin mode。
```

---

### 6.4 Segment generation rules

每個 scene 產生：

```text
segments/{scene_id}.mp4
```

輸入：

```text
audio/{scene_id}.wav
assets/{scene_id}_*.png
```

使用 ffmpeg：

```text
static image + audio → mp4 segment
```

建議輸出：

```text
resolution: resolved render resolution from Section 6.3（default fallback: 1080x1920）
fps: 30
video codec: libx264
pixel format: yuv420p
audio codec: aac
shortest: true
```

若 audio duration 比 visual duration 長，以 audio 為準，static image 持續到 audio 結束。

---

### 6.5 Composition rules

將所有 segments 依 `asset_plan.plans` 順序 concat。

輸出：

```text
final/output.mp4
final/output_subtitles.srt  # optional but recommended
```

使用 ffmpeg concat demuxer 或 concat filter。

MVP2C-thin 不加 BGM，除非 config 已明確提供且測試覆蓋。預設：

```text
BGM disabled
```

---

## 7. Output contracts

MVP2C-thin 完成後，以下 artifact 應存在：

```text
runs/{project_id}/audio/{scene_id}.wav
runs/{project_id}/assets/{scene_id}_*.png
runs/{project_id}/segments/{scene_id}.mp4
runs/{project_id}/final/output.mp4
runs/{project_id}/media_generation_report.json
```

建議額外輸出：

```text
runs/{project_id}/media_metadata/audio.json
runs/{project_id}/media_metadata/visuals.json
runs/{project_id}/media_metadata/segments.json
runs/{project_id}/media_metadata/composition.json
```

`project_state.assets` 應更新摘要與路徑，不嵌入大型內容。

示例：

```json
{
  "assets": {
    "audio_manifest": "media_metadata/audio.json",
    "visual_manifest": "media_metadata/visuals.json",
    "segment_manifest": "media_metadata/segments.json",
    "media_generation_report": "media_generation_report.json"
  },
  "final_video": {
    "path": "final/output.mp4",
    "status": "draft"
  }
}
```

---

## 8. Stage integration

MVP2C-thin 涉及兩個 stage：

```text
asset_generation
composition
```

### 8.1 asset_generation stage

輸入：

```text
asset_plan.json
figures.json optional
```

輸出：

```text
audio/*.wav
assets/*.png
segments/*.mp4
media_generation_report.json
media_metadata/*.json
```

成功條件：

```text
- 每個 scene 有 audio
- 每個 scene 有 visual PNG
- 每個 scene 有 segment MP4
- segment_count == scene_count
```

### 8.2 composition stage

輸入：

```text
segments/*.mp4
```

輸出：

```text
final/output.mp4
```

成功條件：

```text
- final/output.mp4 exists
- file size > 0
- ffprobe can read duration if ffprobe available
```

### 8.3 Dependency rules

```text
asset_generation requires asset_preparation == done.
composition requires asset_generation == done.
```

MVP2C-thin 不要求 final_review。

---

## 9. Validation / quality gates

### 9.1 Hard fail

```text
- asset_plan.json missing
- asset_plan schema invalid
- TTS fails for any scene after retry（整體 stage failed，不繼續其餘 scene）
- visual placeholder cannot be generated
- segment generation fails
- composition fails
- final/output.mp4 missing or empty
```

### 9.2 Warning only

```text
- figures.json missing
- paper figure image_path missing → text_card fallback
- diagram/metaphor/chart source unsupported in thin mode → text_card fallback
- subtitle_text long for visual placeholder
- ffprobe unavailable, duration not recorded
```

### 9.3 Thin quality report

MVP2C-thin 不需要 full reviewer，但需要 media generation report：

```text
- audio_count
- visual_count
- segment_count
- fallback_visual_count
- warnings
- final_video_path
```

---

## 10. Tests

### 10.1 Schema tests

File:

```text
tests/test_media_schema.py
```

Must test：

```text
- GeneratedAudio roundtrip
- GeneratedVisual roundtrip
- GeneratedSegment roundtrip
- CompositionResult roundtrip
- MediaGenerationReport roundtrip
```

---

### 10.2 TTS service tests

File:

```text
tests/test_tts_service_thin.py
```

Must test：

```text
- Edge-TTS command/request construction
- voice fallback order
- output path audio/{scene_id}.wav
- tts_plan.text is used exactly
- duration reading from actual .wav file（happy path）
- duration fallback to estimated_duration_sec when .wav unreadable（fallback path）
- failure after retries marks stage failed
```

Use fake TTS backend for tests. Do not require network access.

> **Fake TTS backend 規格**：
>
> fake backend 必須產出一個合法的靜音 .wav 檔（至少 0.5 秒），讓 duration-from-file 的 happy path 可被測試。
> 建議用 Python `wave` 模組產生最小合法 .wav。
>
> 測試中必須分開覆蓋兩個 path：
> ```text
> test case A：fake backend 產出合法 .wav → duration 由音檔讀取（happy path）
> test case B：duration 讀取失敗 → fallback 到 estimated_duration_sec（fallback path）
> ```
> 若 test case B 只靠靜音 .wav 難以模擬，可 mock duration reader 回傳 None 來觸發 fallback。

---

### 10.3 Visual placeholder tests

File:

```text
tests/test_visual_placeholder.py
```

Must test：

```text
- text_card PNG is generated
- static_background PNG is generated
- paper figure with image_path is placed on canvas
- paper figure caption_without_image falls back to text_card
- diagram/metaphor/chart falls back to text_card in thin mode
- output path is inside run_dir
```

---

### 10.4 Segment composer tests

File:

```text
tests/test_segment_composer.py
```

Must test：

```text
- builds ffmpeg command for image+audio segment
- output path segments/{scene_id}.mp4
- handles spaces in paths
- failure returns useful error
```

Use small fixture audio/image or mock subprocess.

---

### 10.5 Video service tests

File:

```text
tests/test_video_service_thin.py
```

Must test：

```text
- builds concat command
- preserves segment order from asset_plan
- writes final/output.mp4
- handles missing segment as failure
```

Use mock subprocess unless ffmpeg fixture test is stable in local environment.

---

### 10.6 Pipeline tests

File:

```text
tests/test_mvp2c_thin_pipeline.py
```

Must test：

```text
- run --stage asset_generation creates audio/ assets/ segments/ metadata
- asset_generation status becomes done
- run --stage composition creates final/output.mp4
- composition status becomes done
- missing asset_plan fails clearly
- old project migration adds asset_generation / composition keys without resetting prior stages
```

---

## 11. Manual smoke plan

Use a HARDEN-1-passed project or fixture project.

Recommended command sequence:

```bash
.\.venv-win\Scripts\python.exe -m p2s_core.cli status --project <project_id>
.\.venv-win\Scripts\python.exe -m p2s_core.cli run --stage asset_generation --project <project_id>
.\.venv-win\Scripts\python.exe -m p2s_core.cli run --stage composition --project <project_id>
```

Expected status after smoke:

```text
asset_preparation  done
asset_generation   done
composition        done
final_review       pending
```

Expected output:

```text
runs/<project_id>/final/output.mp4
```

Manual smoke should inspect:

```text
- output.mp4 exists
- output.mp4 plays
- audio is audible
- scene order is correct
- text cards are readable enough for thin mode
```

---

## 12. Day-by-day sprint plan

### Day 1：Schemas and media metadata contracts

```text
- Add media schemas.
- Add schema exports.
- Add schema roundtrip tests.
- Create media_metadata path conventions.
```

Verification:

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/test_media_schema.py -v
```

---

### Day 2：TTS service thin

```text
- Implement Edge-TTS backend wrapper.
- Add fake backend for tests.
- Generate audio/{scene_id}.wav.
- Read or estimate duration.
```

Verification:

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/test_tts_service_thin.py -v
```

---

### Day 3：Visual placeholder generation

```text
- Implement text_card renderer.
- Implement static background renderer.
- Implement paper figure canvas placement.
- Add fallback behavior.
```

Suggested implementation:

```text
Use Pillow for PNG generation.
Add pillow to requirements if not already present.
```

Verification:

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/test_visual_placeholder.py -v
```

---

### Day 4：Segment composer

```text
- Implement image+audio → MP4 segment with ffmpeg subprocess.
- Store ffmpeg command in GeneratedSegment metadata.
- Add failure handling.
```

Verification:

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/test_segment_composer.py -v
```

---

### Day 5：Composition

```text
- Implement segment concat.
- Output final/output.mp4.
- Add CompositionResult.
- Optional: output basic .srt.
```

Verification:

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/test_video_service_thin.py -v
```

---

### Day 6：Pipeline / CLI integration

```text
- Wire asset_generation stage.
- Wire composition stage.
- Update project_state assets / final_video.
- Add migration for old projects.
- Add pipeline tests.
```

Verification:

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/test_mvp2c_thin_pipeline.py -v
```

---

### Day 7：Full regression, manual smoke, status

```text
- Run full regression.
- Run manual smoke on HARDEN-1-passed project.
- Create MVP2C_THIN_STATUS.md.
- Confirm HARDEN-3 remains next mandatory checkpoint.
```

Verification:

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/ -v
```

---

## 13. Status template

MVP2C-thin must create `MVP2C_THIN_STATUS.md` using the standard v8.2 status structure:

```markdown
# MVP2C-thin Status

Last updated: YYYY-MM-DD

## Contract complete
- Completed artifact / schema / CLI / service contract

## Current verification
- Focused tests
- Full regression
- Manual smoke

## Known quality gaps
- Remaining data quality / media quality / edge-case gaps

## Hardening backlog
- Items deferred to HARDEN-3 / full MVP2C / MVP3

## Recommended next step
- HARDEN-3: Media Quality / Composition
```

---

## 14. Acceptance criteria

MVP2C-thin is accepted only if all are true:

```text
[ ] Media schemas exist and pass roundtrip tests.
[ ] `asset_generation` stage exists and consumes asset_plan.json.
[ ] `composition` stage exists and consumes segments/*.mp4.
[ ] Every scene produces audio/{scene_id}.wav.
[ ] Every scene produces assets/{scene_id}_*.png.
[ ] Every scene produces segments/{scene_id}.mp4.
[ ] final/output.mp4 is produced.
[ ] final/output.mp4 is non-empty and playable in manual smoke.
[ ] `media_generation_report.json` is produced.
[ ] media metadata manifests are produced or equivalent metadata is recorded.
[ ] project_state.stages.asset_generation.status == done.
[ ] project_state.stages.composition.status == done.
[ ] project_state.final_video.path == "final/output.mp4".
[ ] paper_figure scenes can use figures.json when image_path exists.
[ ] paper_figure scenes fallback cleanly when image_path is missing.
[ ] diagram/metaphor/chart sources fallback to text_card in thin mode.
[ ] No ComfyUI / RunningHub / VRM / Playwright / AI image generation is introduced.
[ ] Full pytest regression passes.
[ ] Manual smoke on a HARDEN-1-passed project passes.
[ ] MVP2C_THIN_STATUS.md is created.
[ ] Recommended next step is HARDEN-3, not MVP2C-full.
```

---

## 15. Post-MVP2C-thin handoff

After MVP2C-thin acceptance, do **not** proceed directly to MVP2C-full.

The next checkpoint is mandatory:

```text
HARDEN-3: Media Quality / Composition
```

HARDEN-3 should cover:

```text
- TTS timing and duration consistency
- subtitle readability
- text-card / figure-card layout quality
- segment composition stability
- audio loudness
- final MP4 compatibility
- fallback quality reporting
```

Only after HARDEN-3 should the project decide whether to proceed to:

```text
Option A: MVP2C-full media generation
Option B: MVP3 reviewer committee
Option C: MVP4 inspection UI prototype
```

---

## 16. Final instruction to coding agent

Implement MVP2C-thin as a minimal playable video pipeline.

Hard constraints:

```text
- Read asset_plan.json.
- Do not infer scene strategy from scenes.json.
- Generate real Edge-TTS audio, but no voice cloning.
- Generate simple PNG visuals, but no AI images.
- Use ffmpeg for static image + audio segments and final concat.
- Do not introduce ComfyUI / VRM / Playwright.
- Keep output paths deterministic.
- Keep all outputs schema-validated and test-covered.
- Preserve prior stage statuses during migration.
- Produce final/output.mp4.
- After completion, hand off to HARDEN-3, not MVP2C-full.
```

Expected major artifacts:

```text
runs/{project_id}/audio/*.wav
runs/{project_id}/assets/*.png
runs/{project_id}/segments/*.mp4
runs/{project_id}/final/output.mp4
runs/{project_id}/media_generation_report.json
docs/sprints/MVP2/MVP2C_THIN/MVP2C_THIN_STATUS.md
```
