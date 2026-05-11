# IMPLEMENTATION PLAN — P2S MVP2B：Asset & Render Preparation

> 文件定位：本文件是 **MVP2B sprint contract**，可直接交給 coding agent / Codex / Claude Code 作為開工依據。  
> 本階段目標是把已通過 MVP2A / MVP2A-2 gate 的 presentation scenes 轉換成 `asset_plan.json`。  
> **MVP2B 只做資產規劃，不做真實媒體生成。**

---

## 0. 當前前提

MVP0、MVP1、MVP2A、MVP2A-2 已經建立了目前需要的前置資料鏈：

```text
source.pdf
→ extracted_text.md
→ claims.json
→ narrative_plan.json
→ scenes.json
→ presentation_plan.json
→ optional scenes_rewritten.json
```

目前狀態：

```text
presentation_planning  done
llm_quality_rewrite    done 或 pending/skip
asset_preparation      pending
```

MVP2A 已經完成：

```text
runs/{project_id}/narrative_plan.json
runs/{project_id}/scenes.json
runs/{project_id}/presentation_plan.json
runs/{project_id}/reviews/presentation_review_rev001.json
```

MVP2A-2 可能額外完成：

```text
runs/{project_id}/scenes_rewritten.json
runs/{project_id}/reviews/llm_quality_rewrite_review_rev001.json
```

並且當 rewrite gate 通過時：

```json
{
  "active_scene_source": "scenes_rewritten.json"
}
```

因此 MVP2B 的第一條硬規則是：

> **MVP2B must read `project_state.active_scene_source`; do not hardcode `scenes.json`.**

---

## 1. MVP2B 核心目標

MVP2B 的目標不是生成圖片、聲音或影片，而是產生後續 MVP2C 可以執行的資產計畫：

```text
presentation_plan.json
+ active scene source
+ claims.json
+ extracted figures metadata
+ persona / style / voice config
→ asset_plan.json
```

`asset_plan.json` 必須回答每一幕：

```text
1. 這幕要不要 TTS？用什麼 voice profile？輸出預期路徑是什麼？
2. 這幕要不要視覺素材？如果要，是 paper figure、diagram、metaphor image、text card，還是 static background？
3. 這幕有哪些 fallback choices？
4. 這幕該用哪種 template hint？
5. 這幕是否需要後續人工或 reviewer 注意？
```

MVP2B 的完成標誌：

```text
runs/{project_id}/asset_plan.json exists
project_state.stages.asset_preparation.status == "done"
```

---

## 2. Non-goals：MVP2B 明確不做

MVP2B 不做任何真實媒體生成。

禁止在本 sprint 中實作：

```text
- Edge-TTS 真實語音生成
- GPT-SoVITS / CosyVoice / Index-TTS 呼叫
- image generation
- ComfyUI / RunningHub / SD / Flux 呼叫
- VRM rendering
- lip sync
- motion generation
- HTML frame rendering
- Playwright rendering
- ffmpeg segment generation
- final video composition
- Streamlit UI
- auto-fix loop
- LLM-backed asset planning
```

本階段允許產生：

```text
- TTS placeholder plan
- visual asset placeholder plan
- paper figure selection plan
- fallback chain
- template hint
- asset preparation quality report
```

---

## 3. 設計原則

### 3.1 Presentation Planning owns strategy

MVP2A 已經決定：

```text
presenter_mode
visual_focus
asset_policy
asset_type_hint
background_mode
```

MVP2B 不應重新決定這些欄位。MVP2B 的任務是依照這些欄位產生具體素材計畫。

正確責任邊界：

```text
MVP2A:
  決定這一幕的呈現策略。

MVP2B:
  根據呈現策略，準備後續生成所需的 asset plan。

MVP2C:
  根據 asset plan，實際生成 audio / visual / frame / segment。
```

### 3.2 Stable contract over quality tuning

MVP2B 優先建立穩定資料合約，而不是追求完美素材選擇。

可接受：

```text
- figure selection 還很簡單
- template hint 還是 deterministic
- diagram prompt 還很樸素
- fallback chain 還是 rule-based
```

不可接受：

```text
- output schema 不穩
- scene 對不上 presentation_plan
- hardcode scenes.json
- asset_policy=none 卻硬塞素材
- asset_policy=required 卻沒有 warning 或 plan
- MVP2B 偷偷呼叫真實 TTS / image / ffmpeg
```

### 3.3 Every scene must have a plan

即使某一幕完全不需要視覺素材，也要有 asset plan。

例如：

```json
{
  "scene_id": "scene_001",
  "visual_plan": {
    "asset_source": "none",
    "fallback_chain": ["text_card", "static_clean_background"]
  }
}
```

---

## 4. 新增 / 修改檔案清單

### 4.1 Models

新增或擴充：

```text
p2s_core/models/asset_plan.py
```

若專案目前有集中式 model export，記得同步：

```text
p2s_core/models/__init__.py
```

### 4.2 Service

新增：

```text
p2s_core/services/asset_preparation.py
```

或若現有架構已經有：

```text
p2s_core/services/visual_planning.py
```

則可以在 `visual_planning.py` 中加入 MVP2B 主邏輯，但建議用 `asset_preparation.py` 作為 stage service 入口，避免和未來 MVP2C 的 media generation 混淆。

### 4.3 Pipeline / CLI

修改：

```text
p2s_core/pipelines/paper_summary.py
p2s_core/cli.py
p2s_core/models/project_state.py
```

目標：

```text
- stage contract 加入 asset_preparation
- CLI 支援 `run --stage asset_preparation`
- status 顯示 asset_preparation
- migration 對舊 project_state 補 stage key
- migration 不重設既有 stage 狀態，尤其不可把已 done 的 llm_quality_rewrite 改回 pending
```

### 4.4 Tests

新增：

```text
tests/test_asset_plan_schema.py
tests/test_asset_preparation_service.py
tests/test_asset_preparation_pipeline.py
```

可視情況擴充：

```text
tests/test_mvp2b_pipeline_smoke.py
```

### 4.5 Docs

新增 sprint 文件：

```text
docs/sprints/MVP2/MVP2B/IMPLEMENTATION_PLAN_MVP2B.md
```

完成後新增：

```text
docs/sprints/MVP2/MVP2B/MVP2B_STATUS.md
```

---

## 5. Schema 設計

### 5.1 AssetPlanBundle

```python
class AssetPlanBundle(BaseModel):
    project_id: str
    scene_source: str
    presentation_plan_path: str = "presentation_plan.json"
    plans: list[SceneAssetPlan]
    quality_report: AssetPlanQualityReport
    created_at: str
    version: str = "mvp2b_v1"
```

說明：

```text
scene_source:
  來自 project_state.active_scene_source。
  可能是 scenes.json 或 scenes_rewritten.json。

plans:
  每個 scene 一個 SceneAssetPlan。

quality_report:
  整體統計與 warnings。
```

---

### 5.2 SceneAssetPlan

```python
class SceneAssetPlan(BaseModel):
    scene_id: str
    purpose: str
    claim_ids: list[str]

    voice_text: str
    subtitle_text: str

    presenter_mode: str
    visual_focus: str
    asset_policy: str
    asset_type_hint: str
    background_mode: str

    tts_plan: TTSPlan
    visual_plan: VisualAssetPlan
    render_plan: RenderPlan

    warnings: list[str] = []
    notes: str | None = None
```

原則：

```text
- 保留 MVP2A 的 scene skeleton 關鍵欄位。
- 不允許 MVP2B 修改 voice_text / subtitle_text。
- 不允許 MVP2B 修改 presenter_mode / visual_focus / asset_policy / asset_type_hint / background_mode。
- MVP2B 只能產生 plan，不改 presentation decision。
```

---

### 5.3 TTSPlan

```python
class TTSPlan(BaseModel):
    enabled: bool = True
    backend: str = "edge_tts"
    voice: str | None = None
    speed: float = 1.0
    pitch: float | None = None
    emotion: str | None = None
    text: str
    output_path: str
    estimated_duration_sec: float | None = None
    placeholder_only: bool = True
    notes: str | None = None
```

MVP2B 不真實生成 TTS，所以：

```python
placeholder_only = True
```

`estimated_duration_sec` 可以先用簡單估算：

```text
中文：每秒約 4~5 字
英文：每秒約 2.3~2.8 words
```

第一版可接受 deterministic approximation，例如：

```python
estimated_duration_sec = max(2.0, len(voice_text) / 4.5)
```

但不要讓估算影響後續 reviewer gate，只作為 MVP2C 參考。

---

### 5.4 VisualAssetPlan

```python
class VisualAssetPlan(BaseModel):
    enabled: bool
    asset_source: Literal[
        "none",
        "paper_figure",
        "diagram_prompt",
        "metaphor_image_prompt",
        "chart_prompt",
        "text_card",
        "static_background",
    ]
    asset_type_hint: str
    asset_intent: str | None = None

    selected_figure_ids: list[str] = []
    figure_selection_reason: str | None = None

    visual_prompt: str | None = None
    fallback_chain: list[str]
    output_placeholder: str | None = None

    risk_flags: list[str] = []
    notes: str | None = None
```

> **`fallback_chain` 型別語義說明（重要）：**
>
> `fallback_chain` 是 **generation strategy hint**，不是 `asset_source` 的 enum subset。
> 其中的字串值（例如 `"html_diagram"`、`"ai_generated"`）代表 MVP2C 的生成策略，
> 不能直接當作 `asset_source` 值使用。MVP2C 負責解譯這些 hint 並決定實際行為。
>
> MVP2B 不應嘗試把 `fallback_chain` 的值對應到 `asset_source` Literal。
> 如果 MVP2C 想驗證 fallback_chain 的值，應另行定義 `FallbackStrategy` 型別（MVP2C 的事，MVP2B 不做）。

---

### 5.5 RenderPlan

```python
class RenderPlan(BaseModel):
    template_hint: str
    layout_mode: Literal[
        "presenter_only",
        "presenter_with_overlay",
        "asset_focus",
        "text_card",
        "static_clean",
    ]
    resolution: str = "1080x1920"
    fps: int = 30
    background_mode: str
    subtitle_mode: str = "one_sentence"
    output_segment_placeholder: str
    notes: str | None = None
```

MVP2B 不使用 Playwright / ffmpeg，只填 placeholder。

---

### 5.6 AssetPlanQualityReport

```python
class AssetPlanQualityReport(BaseModel):
    scene_count: int
    tts_enabled_count: int
    visual_enabled_count: int

    # Counts by original scene intent.
    # required_asset_count = number of scenes where Scene.asset_policy == "required".
    # optional_asset_count = number of scenes where Scene.asset_policy == "optional".
    # no_asset_count = number of scenes where Scene.asset_policy == "none".
    #
    # Important: no_asset_count is NOT derived from VisualAssetPlan.asset_source == "none".
    # A scene may have asset_policy="optional" but still resolve to asset_source="none" or
    # "text_card" after fallback; that must not be counted as no_asset_count.
    required_asset_count: int
    optional_asset_count: int
    no_asset_count: int

    # Counts by resolved visual plan / fallback result.
    paper_figure_count: int
    diagram_prompt_count: int
    metaphor_prompt_count: int
    text_card_count: int
    static_background_count: int

    warnings: list[str] = []
```

Counting rule summary:

```text
no_asset_count      → count scenes with asset_policy == "none"
visual_enabled_count → count scenes whose VisualAssetPlan.enabled == true
asset_source counts → count resolved VisualAssetPlan.asset_source values
```

This distinction matters because these cases are different:

```text
asset_policy="none"      + asset_source="none"      → no_asset_count += 1
asset_policy="optional"  + asset_source="none"      → no_asset_count unchanged; optional_asset_count += 1
asset_policy="optional"  + asset_source="text_card" → optional_asset_count += 1; text_card_count += 1
asset_policy="required"  + asset_source="text_card" → required_asset_count += 1; text_card_count += 1; warning required if this is fallback
```

---

## 6. Asset planning rules

### 6.1 Scene source resolution

MVP2B 採用明確 fallback policy：

> **Policy: fallback with warning.**
> 如果 `project_state.active_scene_source` 指向非 `scenes.json` 的檔案，但該檔案不存在，MVP2B 會 fallback 到 `scenes.json`。如果 `scenes.json` 也不存在，stage failed。

MVP2B 必須使用以下邏輯：

```python
requested_scene_source = project_state.active_scene_source or "scenes.json"
requested_scene_path = run_dir / requested_scene_source

if requested_scene_path.exists():
    scene_source = requested_scene_source
    scene_path = requested_scene_path
elif requested_scene_source != "scenes.json" and (run_dir / "scenes.json").exists():
    scene_source = "scenes.json"
    scene_path = run_dir / "scenes.json"
    warning = (
        f"active_scene_source {requested_scene_source!r} was missing; "
        "fell back to 'scenes.json'."
    )
else:
    fail stage
```

Warning requirements:

```text
- The fallback warning must be written to AssetPlanQualityReport.warnings.
- The same warning must be surfaced in the stage output / CLI output.
- If StageState already supports human_notes or warnings, write it there too.
- Do not silently pass when active_scene_source points to a missing file.
```

Reason: fallback is safer for old / partially migrated projects, but the user must see that MVP2B did not consume the requested rewritten scene source.

---

### 6.2 Presentation alignment validation

讀取：

```text
presentation_plan.json
active scene source
```

檢查：

```text
- scene ids 完全一致，或至少 presentation_plan 中每個 scene_id 都能在 scenes 中找到。
- 不允許 duplicated scene_id。
- 不允許 presentation_plan 引用 unknown scene_id。
- 若 active scenes 多出 presentation_plan 沒有的 scene，warning 或 failed，視現有架構選擇。
```

建議 MVP2B 第一版採取嚴格規則：

```text
scene_id set must match exactly.
```

原因：避免後續 MVP2C 生成時才發現 scene 對不上。

---

### 6.3 TTS plan rules

每個 scene 都建立 `tts_plan`。

```text
enabled = True
text = scene.voice_text
output_path = audio/{scene_id}.wav
placeholder_only = True
```

voice 來源優先序：

```text
1. project_state.persona.voice_profile_id / loaded persona voice profile
2. config.tts.default_voice
3. fallback: "zh-TW-HsiaoChenNeural"
```

若無法載入 persona voice profile，不應失敗；記錄 warning，使用 config fallback。

---

### 6.4 Visual plan rules

根據 `asset_policy` 和 `asset_type_hint` 決定。

#### Case A: asset_policy = none

```text
visual_plan.enabled = False
asset_source = "none"
fallback_chain = ["text_card", "static_background"]
template_hint = 根據 visual_focus / background_mode 選 static_clean 或 presenter_only
```

不得選 paper figure、diagram、metaphor image。

---

#### Case B: asset_type_hint = paper_figure

```text
visual_plan.enabled = True
asset_source = "paper_figure"
selected_figure_ids = select_figures(scene, figures)
fallback_chain = ["paper_figure", "text_card", "static_background"]
```

若找不到 figure：

```text
- asset_policy == required：
    asset_source 維持 "paper_figure"（保留原始意圖）
    selected_figure_ids = []
    warnings += high severity warning
    stage 不 fail，但 MVP2C 讀到空 selected_figure_ids 必須自行處理 fallback
    quality_report.paper_figure_count += 1（依解析出的 asset_source 計數，不依是否找到）

- asset_policy == optional：
    asset_source 降級為 "text_card"
    selected_figure_ids = []
    warnings += low severity warning
    quality_report.text_card_count += 1
```

> **`asset_source` 計數規則（重要）：**
> `paper_figure_count` 等 asset_source 計數以 **resolved `VisualAssetPlan.asset_source`** 為準。
> 因此 required + not found → `asset_source="paper_figure"` → `paper_figure_count += 1`。
> optional + not found → `asset_source="text_card"` → `text_card_count += 1`。

第一版 figure selection 可以簡單：

```text
- 以 scene.asset_intent / voice_text / claim text 關鍵詞對 figure caption 做 substring / token overlap。
- 若沒有 caption metadata，就選空，不要亂選。
```

---

#### Case C: asset_type_hint = diagram

```text
asset_source = "diagram_prompt"
visual_prompt = deterministic diagram prompt
fallback_chain = ["html_diagram", "text_card", "static_background"]
```

prompt 第一版可以很保守：

```text
Create a clean educational diagram for this scene: {asset_intent}. Use minimal labels, no decorative clutter.
```

---

#### Case D: asset_type_hint = metaphor_image

```text
asset_source = "metaphor_image_prompt"
visual_prompt = deterministic metaphor prompt
fallback_chain = ["ai_generated", "text_card", "static_background"]
```

注意：MVP2B 只產生 prompt，不呼叫 image model。

---

#### Case E: asset_type_hint = chart

```text
asset_source = "chart_prompt"
visual_prompt = deterministic chart prompt
fallback_chain = ["html_diagram", "text_card", "static_background"]
```

若沒有具體數據，不要假造數字。

---

#### Case F: asset_type_hint = none, asset_policy = optional

```text
asset_source = "text_card" 或 "static_background"
fallback_chain = ["text_card", "static_background"]
```

原則：不要為了有素材而硬塞圖。

---

#### Case G: asset_type_hint = none, asset_policy = required

```text
visual_plan.enabled = True
asset_source = "text_card"
fallback_chain = ["text_card", "static_background"]
warnings += ["asset_policy=required but asset_type_hint=none; treating as text_card. Review scene intent."]
```

說明：`required + none` 是 MVP2A 輸出的邊緣組合，表示簡報策略聲稱必須有素材，但沒有指定類型。
MVP2B 視同使用 `text_card`，但必須發出 warning 提醒人工確認，不能靜默降級。
`required_asset_count` 仍然 +1（依 asset_policy 計數）。

---

### 6.5 Template hint rules

根據 `visual_focus` 決定 `template_hint`：

```text
visual_focus = presenter
  → presenter_only_clean

visual_focus = supporting_asset
  → presenter_with_overlay_clean

visual_focus = split
  → split_presenter_asset_clean

visual_focus = asset_fullscreen
  → asset_fullscreen_caption_clean

visual_focus = text_card
  → text_card_clean
```

如果 `presenter_mode = off_screen` 且 `visual_focus = presenter`，要 warning，並 fallback：

```text
layout_mode = text_card
template_hint = "text_card_clean"
```

> **`output_placeholder` 設值規則：**
>
> MVP2C 需要知道生成素材的預期存放路徑。MVP2B 必須按以下規則設值，
> 不可全部留 `null`（否則違反「MVP2C should not need to infer from scratch」原則）：
>
> ```text
> asset_source == "paper_figure"         → output_placeholder = "assets/{scene_id}_figure.png"
> asset_source == "diagram_prompt"       → output_placeholder = "assets/{scene_id}_diagram.png"
> asset_source == "metaphor_image_prompt"→ output_placeholder = "assets/{scene_id}_metaphor.png"
> asset_source == "chart_prompt"         → output_placeholder = "assets/{scene_id}_chart.png"
> asset_source == "text_card"            → output_placeholder = "assets/{scene_id}_textcard.png"
> asset_source == "static_background"    → output_placeholder = "assets/{scene_id}_bg.png"
> asset_source == "none"                 → output_placeholder = null
> ```

---

## 7. `asset_plan.json` example

> Counting note: in this example, `optional_asset_count = 1` while `visual_enabled_count = 0`.
> This is intentional. `optional_asset_count` counts the original scene intent (`asset_policy == "optional"`), while `visual_enabled_count` counts the resolved plan (`VisualAssetPlan.enabled == true`).
> Tests must not assume these two counters add up or must match.

```json
{
  "project_id": "mvp1_real_smoke",
  "scene_source": "scenes_rewritten.json",
  "presentation_plan_path": "presentation_plan.json",
  "version": "mvp2b_v1",
  "created_at": "2026-05-08T12:00:00Z",
  "plans": [
    {
      "scene_id": "scene_001",
      "purpose": "hook",
      "claim_ids": ["claim_001"],
      "voice_text": "這篇研究想問：短短一段生理訊號，能不能幫我們看見情緒的線索？",
      "subtitle_text": "生理訊號裡，可能藏著情緒線索。",
      "presenter_mode": "speaking_on_camera",
      "visual_focus": "presenter",
      "asset_policy": "optional",
      "asset_type_hint": "none",
      "background_mode": "static_clean",
      "tts_plan": {
        "enabled": true,
        "backend": "edge_tts",
        "voice": "zh-TW-HsiaoChenNeural",
        "speed": 1.0,
        "pitch": null,
        "emotion": "gentle",
        "text": "這篇研究想問：短短一段生理訊號，能不能幫我們看見情緒的線索？",
        "output_path": "audio/scene_001.wav",
        "estimated_duration_sec": 6.2,
        "placeholder_only": true,
        "notes": "MVP2B placeholder only; actual synthesis in MVP2C."
      },
      "visual_plan": {
        "enabled": false,
        "asset_source": "none",
        "asset_type_hint": "none",
        "asset_intent": null,
        "selected_figure_ids": [],
        "figure_selection_reason": null,
        "visual_prompt": null,
        "fallback_chain": ["text_card", "static_background"],
        "output_placeholder": null,
        "risk_flags": [],
        "notes": "No external visual asset needed."
      },
      "render_plan": {
        "template_hint": "presenter_only_clean",
        "layout_mode": "presenter_only",
        "resolution": "1080x1920",
        "fps": 30,
        "background_mode": "static_clean",
        "subtitle_mode": "one_sentence",
        "output_segment_placeholder": "segments/scene_001.mp4",
        "notes": null
      },
      "warnings": [],
      "notes": null
    }
  ],
  "quality_report": {
    "scene_count": 1,
    "tts_enabled_count": 1,
    "visual_enabled_count": 0,
    "required_asset_count": 0,
    "optional_asset_count": 1,
    "no_asset_count": 0,
    "paper_figure_count": 0,
    "diagram_prompt_count": 0,
    "metaphor_prompt_count": 0,
    "text_card_count": 0,
    "static_background_count": 0,
    "warnings": []
  }
}
```

---

## 8. Stage integration

### 8.1 Stage contract

在 project state stage order 中加入：

```text
extraction
→ claim_extraction
→ narrative_planning
→ presentation_planning
→ llm_quality_rewrite
→ asset_preparation
→ asset_generation
→ composition
→ final_review
```

Dependency is intentionally loose-coupled:

```text
asset_preparation requires presentation_planning == done.
asset_preparation does NOT require llm_quality_rewrite == done.
```

Allowed cases:

```text
Case A: llm_quality_rewrite pending / skipped
  → active_scene_source should normally be scenes.json
  → MVP2B consumes scenes.json

Case B: llm_quality_rewrite done and gate passed
  → active_scene_source should normally be scenes_rewritten.json
  → MVP2B consumes scenes_rewritten.json

Case C: active_scene_source points to a missing rewritten file
  → fallback to scenes.json with visible warning, per Section 6.1
```

Migration rule for older project_state files:

```text
- Migration must add missing stage keys such as asset_preparation and asset_generation.
- Migration must NOT reset or overwrite existing stage records.
- If an old project such as mvp1_real_smoke already has llm_quality_rewrite.status == done, keep it as done.
- Do not rewrite active_scene_source during migration unless the field is missing.
- If active_scene_source is missing, default it to scenes.json.
```

This preserves MVP2A-2 results while allowing MVP2B to run on projects that never used the rewrite stage.

---

### 8.2 Dependency rules

執行 `asset_preparation` 前必須確認：

```text
presentation_planning.status == done
presentation_plan.json exists
resolved scene source exists  # after applying Section 6.1 fallback policy
claims.json exists  # 建議 required，因為 scene claim_ids 可驗證
```

可選：

```text
figures/ exists
```

若 figures 不存在，不能 fail；只要記錄 warning，因為 MVP0/MVP1 extraction 未必已經有穩定 figure extraction。

---

### 8.3 CLI

支援：

```bash
python -m p2s_core.cli run --stage asset_preparation --project <project_id>
```

支援 force：

```bash
python -m p2s_core.cli run --stage asset_preparation --project <project_id> --force
```

成功輸出類似：

```text
asset_preparation: done
output: runs/<project_id>/asset_plan.json
scene_source: scenes_rewritten.json
scene_count: 7
warnings: 0
```

---

## 9. Service design

### 9.1 Public function

```python
def prepare_assets_for_project(run_dir: Path, state: ProjectState, config: Config) -> AssetPlanBundle:
    """Create asset_plan.json from active scenes and presentation_plan.json."""
```

或 async version：

```python
async def prepare_assets_for_project(...) -> AssetPlanBundle:
    ...
```

MVP2B 不需要 LLM，所以 sync function 即可。

---

### 9.2 Internal steps

```text
1. Resolve active scene source.
2. Load scenes bundle.
3. Load presentation_plan.json.
4. Load claims.json.
5. Load figure metadata if available.
6. Validate scene ids and presentation alignment.
7. For each scene:
   7.1 build TTSPlan
   7.2 build VisualAssetPlan
   7.3 build RenderPlan
   7.4 collect warnings
8. Build AssetPlanQualityReport.
9. Write asset_plan.json.
10. Update project_state assets / stages.
```

---

### 9.3 Determinism

MVP2B must be deterministic:

```text
same input files → same asset_plan.json except created_at / code_version
```

不要使用：

```text
- random seed
- LLM call
- external API
- current file discovery beyond run_dir
```

---

## 10. Validation / reviewer logic

MVP2B 不需要完整 LLM reviewer，但需要 deterministic validator。

建議新增：

```text
p2s_core/reviewers/asset_plan_validator.py
```

或放在 service 內部。

### 10.1 Checks

```text
- every scene has exactly one SceneAssetPlan
- no unknown scene_id
- no duplicated scene_id
- asset_policy=none → visual_plan.asset_source must be none/text_card/static_background only
- asset_policy=required → visual_plan.enabled must be true OR warnings must include required asset missing
- paper_figure source with empty selected_figure_ids → warning must be present
- paper_figure source with empty selected_figure_ids + asset_policy=required → asset_source stays "paper_figure"; do NOT silently downgrade to text_card
- paper_figure source with empty selected_figure_ids + asset_policy=optional → asset_source must be "text_card" (downgraded)
- asset_policy=required + asset_type_hint=none → asset_source must be "text_card" and warning must be present
- tts_plan.placeholder_only must be true
- tts_plan.text must equal scene.voice_text
- render_plan.output_segment_placeholder must be set
- output_placeholder must be non-null for asset_source in {paper_figure, diagram_prompt, metaphor_image_prompt, chart_prompt, text_card, static_background}
- output_placeholder must be null when asset_source == "none"
- no asset plan writes to actual existing media files
```

### 10.2 Failure policy

Hard fail：

```text
- missing presentation_plan.json
- requested active_scene_source missing AND scenes.json fallback missing
- scene_id mismatch
- duplicated scene_id
- schema validation failure
```

Warning only：

```text
- requested active_scene_source missing but scenes.json fallback exists
- figures/ missing
- required paper figure not found
- persona voice profile missing, fallback voice used
- asset_intent empty for diagram/metaphor_image
```

---

## 11. Tests

### 11.1 Schema tests

File:

```text
tests/test_asset_plan_schema.py
```

Must test：

```text
- AssetPlanBundle roundtrip JSON serialization
- SceneAssetPlan roundtrip
- TTSPlan placeholder_only default
- VisualAssetPlan allowed asset_source values
- RenderPlan allowed layout modes
- AssetPlanQualityReport counts, including no_asset_count defined by asset_policy == "none" rather than asset_source == "none"
- Example fixture note: `optional_asset_count` and `visual_enabled_count` are independent counters; do not assert that optional scenes imply enabled visuals
```

---

### 11.2 Service tests

File:

```text
tests/test_asset_preparation_service.py
```

Must test：

```text
1. builds asset_plan from scenes.json
2. builds asset_plan from scenes_rewritten.json when active_scene_source points to it
3. asset_policy=none does not select visual asset
4. asset_type_hint=diagram creates diagram_prompt plan
5. asset_type_hint=metaphor_image creates metaphor_image_prompt plan
6. asset_type_hint=paper_figure selects matching figure by caption
7. paper_figure required but no figure found: asset_source stays "paper_figure", selected_figure_ids=[], warning added, paper_figure_count += 1
8. paper_figure optional but no figure found: asset_source falls back to "text_card", text_card_count += 1
9. paper_figure required and figure found: asset_source="paper_figure", selected_figure_ids non-empty, no warning
10. asset_policy=required + asset_type_hint=none: asset_source="text_card", warning added, required_asset_count += 1
11. scene_id mismatch fails
12. duplicated scene_id fails
13. missing non-default active_scene_source falls back to scenes.json and writes the warning to both AssetPlanQualityReport.warnings and CLI/stage output
14. missing active_scene_source and missing scenes.json fails the stage
15. migration preserves existing llm_quality_rewrite status and only adds missing MVP2B/MVP2C stage keys
16. tts_plan.text == scene.voice_text for every scene in the output (read-source consistency)
17. output_placeholder is set (non-null) for asset_source in {paper_figure, diagram_prompt, metaphor_image_prompt, chart_prompt, text_card, static_background}
18. output_placeholder is null when asset_source == "none"
19. presenter_mode=off_screen + visual_focus=presenter produces warning and layout_mode=text_card + template_hint=text_card_clean
```

---

### 11.3 Pipeline / CLI tests

File:

```text
tests/test_asset_preparation_pipeline.py
```

Must test：

```text
1. `run --stage asset_preparation` writes asset_plan.json
2. project_state.stages.asset_preparation.status becomes done
3. status command shows asset_preparation done
4. --force rewrites asset_plan.json safely
5. old project migration adds asset_preparation stage key
```

---

### 11.4 Regression command

Use the project-local Windows runtime:

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/ -v
```

Known warning：

```text
pytest-cache-files-* permission warning is already mitigated and non-blocking.
```

---

## 12. Manual real-paper smoke

Use existing project:

```bash
.\.venv-win\Scripts\python.exe -m p2s_core.cli status --project mvp1_real_smoke
```

Expected before MVP2B:

```text
presentation_planning  done
llm_quality_rewrite    done
asset_preparation      pending
```

Run:

```bash
.\.venv-win\Scripts\python.exe -m p2s_core.cli run --stage asset_preparation --project mvp1_real_smoke
```

Expected after MVP2B:

```text
asset_preparation: done
asset_plan.json: created
scene_source: scenes_rewritten.json
```

Then verify:

```bash
.\.venv-win\Scripts\python.exe -m p2s_core.cli status --project mvp1_real_smoke
```

Expected:

```text
presentation_planning  done
llm_quality_rewrite    done
asset_preparation      done
asset_generation       pending
```

Inspect:

```text
runs/mvp1_real_smoke/asset_plan.json
```

Must contain one plan per scene.

---

## 13. Acceptance criteria

MVP2B is accepted only if all are true:

```text
[ ] Asset plan schemas exist and pass roundtrip tests.
[ ] `asset_preparation` stage exists in stage contract.
[ ] CLI supports `run --stage asset_preparation`.
[ ] MVP2B reads `project_state.active_scene_source`.
[ ] MVP2B supports both `scenes.json` and `scenes_rewritten.json`.
[ ] `asset_plan.json` is created.
[ ] Every scene has exactly one SceneAssetPlan.
[ ] Every scene has a TTS placeholder plan.
[ ] tts_plan.text equals scene.voice_text for every scene.
[ ] Every scene has a visual plan, even if visual is disabled.
[ ] output_placeholder is non-null for all asset_source values except "none".
[ ] `asset_policy=none` does not force visual assets.
[ ] `asset_policy=required` + `asset_type_hint=none` produces text_card plan with warning.
[ ] Required visual assets produce either a concrete plan or an explicit warning.
[ ] paper_figure required + not found: asset_source stays "paper_figure", warning present.
[ ] paper_figure optional + not found: asset_source falls back to "text_card".
[ ] No real TTS/image/video generation occurs.
[ ] No ffmpeg/Playwright/ComfyUI/RunningHub dependency is introduced.
[ ] Full pytest regression passes.
[ ] Manual real-paper smoke on `mvp1_real_smoke` passes.
```

---

## 14. Suggested day-by-day sprint plan

### Day 1：Schema

```text
- Add asset_plan.py schemas.
- Export schemas.
- Add schema roundtrip tests.
```

Expected verification:

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/test_asset_plan_schema.py -v
```

---

### Day 2：Asset preparation service skeleton

```text
- Implement active_scene_source resolution using the explicit fallback-with-warning policy from Section 6.1.
- Load scenes / presentation_plan / claims.
- Validate scene alignment.
- Generate minimal one-plan-per-scene asset plan.
```

Expected verification:

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/test_asset_preparation_service.py -v
```

---

### Day 3：TTSPlan + RenderPlan

```text
- Add voice fallback rules.
- Add TTS placeholder path.
- Add estimated duration.
- Add template_hint / layout_mode mapping.
```

---

### Day 4：VisualAssetPlan rules

```text
- asset_policy=none
- paper_figure
- diagram
- metaphor_image
- chart
- optional none fallback
```

---

### Day 5：Figure selection and warnings

```text
- Load figure metadata if available.
- Implement simple caption/token overlap selection.
- Add warnings for missing required figures.
```

---

### Day 6：Pipeline / CLI integration

```text
- Add asset_preparation stage.
- Add CLI support.
- Add old project migration stage key.
- Write asset_plan.json.
- Update project_state stage status.
```

---

### Day 7：Smoke tests and documentation

```text
- Add pipeline smoke tests.
- Run full regression.
- Run manual real-paper smoke.
- Create MVP2B_STATUS.md.
```

---

## 15. Post-MVP2B handoff to MVP2C

MVP2C should begin only after MVP2B acceptance.

MVP2C input contract:

```text
runs/{project_id}/asset_plan.json
```

MVP2C will implement:

```text
asset_plan.json
→ audio/*.wav
→ assets/*.png|mp4
→ frames/*.png
→ segments/*.mp4
→ final/output.mp4
```

MVP2C should not need to infer scene asset strategy from scratch. If it does, MVP2B contract is incomplete.

---

## 16. Final instruction to coding agent

Implement MVP2B as a deterministic asset preparation stage.

Hard constraints:

```text
- Read project_state.active_scene_source.
- Do not hardcode scenes.json.
- Do not call LLMs.
- Do not generate real audio, images, video, HTML frames, or ffmpeg segments.
- Do not mutate scene skeleton fields.
- Do not rewrite presentation ratios.
- Produce asset_plan.json as the only new major artifact.
- Keep all outputs schema-validated and test-covered.
```

Expected final artifact:

```text
runs/{project_id}/asset_plan.json
```

Expected final state:

```text
project_state.stages.asset_preparation.status == "done"
```
