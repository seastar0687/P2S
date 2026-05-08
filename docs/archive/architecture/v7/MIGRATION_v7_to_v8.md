# Migration Log：Architecture Spec v7 → v8

> 這份文件是 v7 → v8 升版的完整記錄。  
> 任何人（或 agentic AI）只需要讀這一份，就能知道：發生了什麼、哪裡衝突、怎麼處理。  
> MVP0 / MVP1 的原始文件保持不動，作為歷史記錄。

---

## 1. 升版時機與原因

- **時間**：2026-05-07，MVP1 完成後、MVP2A 開工前
- **觸發文件**：`P2S_MVP2A_presentation_planning_correction.md`
- **原因**：P2S 的實際成片形式確認為「3D 角色主講 + 素材輔助 + 低干擾背景」，而非純文字腳本。MVP2A 因此從「script generation」改為「Presentation Planning」，此決策需要更新 Architecture Spec 的 schema、pipeline 定義與 MVP 路線圖。

---

## 2. v8 相對於 v7 的變更內容

### 新增
- `SceneDraft` / `Scene`：加入 `presenter_mode` / `visual_focus` / `asset_policy` / `asset_type_hint` / `background_mode` / `asset_intent` / `notes_for_render`
- 新 schema：`PresentationProfile` / `PresentationScene` / `PresentationPlan`（落盤為 `presentation_plan.json`）
- 新模組：`models/presentation.py`
- 新目錄：`presentation_profiles/presenter_first_default/`
- 新 service：`narrative_planning.py`、`presentation_planning.py`
- 新 reviewer：`script_grounding.py`、`style_rule.py`、`presentation_structure.py`
- 新輸出：`narrative_plan.json`、`presentation_plan.json`、`asset_plan.json`
- MVP 路線圖：原 MVP2 拆分為 MVP2A / MVP2B / MVP2C

### Breaking changes
| 項目 | v7 | v8 |
|---|---|---|
| `SceneDraft.scene_id` | `int` | `str` |
| `Scene.scene_id` | `int` | `str` |
| `SceneDraft.visual_type` | `Literal[...] 必填` | `str \| None = None`（deprecated） |
| `Scene.visual_type` | `Literal[...] 必填` | `str \| None = None`（deprecated） |
| Phase 4 stage 名稱 | `script_generation` | `presentation_planning` |
| Phase 5 stage 名稱 | `storyboard_planning` | `asset_preparation` |

### Deprecated（欄位保留，不再使用）
| 欄位 | Schema | 取代者 |
|---|---|---|
| `visual_type` | SceneDraft / Scene | `visual_focus` + `asset_policy` + `asset_type_hint` |
| `visual_intent` | SceneDraft | `asset_intent` |
| `character_presence` | Scene | `presenter_mode` |

---

## 3. 與已實作程式碼的衝突

MVP0（45 tests）與 MVP1（69 tests）已在 v7 spec 下實作完成。v8 的 breaking changes 造成以下衝突：

### C-001｜`scene_id` 型別衝突
- **衝突內容**：v7 spec 定義 `scene_id: int`，MVP0 的 `test_scene_roundtrip` fixture 使用 `scene_id=1`（int）。v8 改為 `str`，Pydantic v2 不自動強轉，會拋 `ValidationError`。
- **影響範圍**：`tests/test_schema.py::test_scene_roundtrip`
- **處理方式**：MVP2A Day 1 更新 schema 時，將 fixture 的 `scene_id=1` 改為 `scene_id="scene_001"`。MVP0 文件保持原樣（它記錄的是當時的決策，v7 spec 當時確實是 int）。
- **處理時機**：MVP2A Day 1

### C-002｜`test_scene_visual_type_consistency` 語意失效
- **衝突內容**：MVP0 的 DoD 特別列出此測試，目的是確保 `SceneDraft.visual_type` 與 `Scene.visual_type` 的 Literal 值完全一致（防止寫成 "static" 而非 "static_template"）。v8 之後 `visual_type` 已 deprecated 為 `str | None`，Literal 約束消失，此測試的設計前提不再成立。
- **影響範圍**：`tests/test_schema.py::test_scene_visual_type_consistency`
- **處理方式**：MVP2A Day 1 將此測試改名為 `test_scene_presentation_fields_consistency`，改為檢查 `presenter_mode` / `visual_focus` / `asset_policy` 的 Literal 在 SceneDraft 與 Scene 之間一致。
- **處理時機**：MVP2A Day 1

### C-003｜`storyboard_planning` stage 名稱衝突
- **衝突內容**：v7 的 Phase 5 stage 名稱為 `storyboard_planning`，v8 改為 `asset_preparation`。若 codebase 中有 hardcode 此 stage 名稱或對應 key，MVP2B 開工時會衝突。
- **影響範圍**：`project_state.json` stage 定義、`BasePipeline` stage 清單
- **處理方式**：MVP2B Day 1 搜尋 codebase 所有 `storyboard_planning` 字串並替換；`storyboard.json` 輸出路徑同步改為 `asset_plan.json`。
- **處理時機**：MVP2B Day 1

### C-004｜Architecture Spec 文件內殘留舊 stage 名稱
- **衝突內容**：v8 升版時 `script_generation` / `storyboard_planning` 在文件多處（dependency chain、project_state 範例、Persona 影響段落、CLI 範例、revision_history 範例、scenes.json 描述）仍殘留舊名稱。
- **影響範圍**：`P2S_redesign_architecture_v8.md` 內文
- **處理方式**：直接在 v8 文件修正，不等 MVP2B。已在本次 v8 cleanup 中全部替換為 `presentation_planning` / `asset_preparation`。
- **處理時機**：✅ 已修（v8 cleanup）

---

## 4. 衝突處理狀態

| ID | 衝突 | 處理時機 | 狀態 |
|---|---|---|---|
| C-001 | `scene_id: int → str` 破壞 roundtrip test | MVP2A Day 1 | ✅ 已修 |
| C-002 | `test_scene_visual_type_consistency` 語意失效 | MVP2A Day 1 | ✅ 已修 |
| C-003 | `storyboard_planning` stage 名稱更名 | MVP2B Day 1 | ✅ 已修 |
| C-004 | Architecture Spec 文件內殘留舊 stage 名稱 | 立即 | ✅ 已修 |

---

## 5. 共存期間規則

v7 與 v8 暫時共存，直到 C-001 / C-002 修復完畢：

- 開發與 agentic AI **以 v8 為準**；v7 僅供對照，不作為實作依據。
- 衝突以**本文件為唯一記錄**，不在其他地方散落說明。
- C-001 / C-002 修復且 pytest 全綠後，執行歸檔（見第 6 節）。

---

## 6. 歸檔計畫

C-001 / C-002 修復、pytest 全綠後：

```
docs/
  archive/
    architecture/
      v7/
        P2S_redesign_architecture_v7.md    ← 舊版原檔，不修改
        MIGRATION_v7_to_v8.md              ← 本文件
```

歸檔後 `P2S_redesign_architecture_v8.md` 成為唯一現行 Architecture Spec。
