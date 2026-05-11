# Migration Log：Architecture Spec v8.1 → v8.2

> 這份文件是 v8.1 → v8.2 升版的完整記錄。  
> 任何人（或 agentic AI）只需要讀這一份，就能知道：發生了什麼、改了什麼、有沒有衝突，以及目前 P2S 的實踐節奏如何調整。

---

## 1. 升版時機與原因

- **時間**：2026-05-08，MVP2B 完成後、MVP2C 開工前。
- **觸發狀態**：`MVP2B_STATUS.md` 顯示 `asset_preparation` 已完成，`asset_plan.json` 已建立，full regression passed；manual real-paper smoke 出現預期 warning：目前 smoke project 沒有 figure metadata，paper figure selection 只能走 fallback。
- **升版原因**：P2S 一直以 MVP sprint 推進，但需要明確區分「MVP contract complete」與「quality complete」。若一路只往下游 media generation 推進，extraction、evidence、figure metadata、reviewer calibration 等資料品質債會被 TTS / image / video generation 放大。因此 v8.2 將「主線 MVP slices + 定期 hardening checkpoints」正式寫入 Architecture Spec，作為長期工程治理原則。

本次升版不是新增某個功能模組，而是補上 P2S 的 **engineering cadence / project governance**：

```text
MVP slice
→ stable schema / artifact / CLI / tests
→ hardening checkpoint
→ real-paper calibration / edge cases / quality gates
→ next downstream MVP
```

---

## 2. v8.2 相對於 v8.1 的變更內容

### 新增（純新增，無 breaking change）

| 項目 | 說明 |
|---|---|
| `10A. Engineering Cadence：MVP Slices + Hardening Checkpoints` | 新增 P2S 的實踐節奏與治理原則 |
| MVP 語義定義 | 明確說明 MVP 在 P2S 中是 engineering slice，不等於產品可用、不等於品質完成 |
| Hardening checkpoint 語義定義 | 明確說明 hardening 負責回補資料品質、邊界案例、golden tests、real-paper calibration、reviewer/gate 穩定性 |
| Hardening 插入時機 | 定義在下游錯誤成本升高前插入，例如 media generation 前 |
| 建議節奏表 | 補上 MVP0–MVP4 對應的 HARDEN-1 到 HARDEN-5 治理建議，並標記 HARDEN-2 不可被默默擠掉 |
| v8.2 當前路線決策 | 明確記錄完整路線：`MVP0 → … → MVP2B → HARDEN-1 → MVP2C-thin → HARDEN-3 → MVP2C-full or MVP3`；路線不在 MVP2C-thin 截斷 |
| Architecture Spec / Implementation Plan 邊界 | 明確規定 hardening 的實作細節應寫進 `IMPLEMENTATION_PLAN_*`，不要塞進 Architecture Spec 主文 |
| 文件名稱更新 | 當前 Architecture Spec 從 `P2S_redesign_architecture_v8.1.md` 升為 `P2S_redesign_architecture_v8.2.md` |

### 無 Breaking Change

v8.2 不修改任何現有 schema、stage name、artifact path、CLI contract 或 reviewer contract。它只新增治理章節與文件版本標記，因此：

```text
- 不需要修改現有程式碼
- 不需要 migration old project_state.json
- 不影響現有 tests
- 不改變 MVP2B artifact contract
- 不改變 v8.1 CodeVersion metadata 設計
```

---

## 3. 與已實作程式碼的衝突

**無程式碼衝突。** v8.2 是 Architecture Spec 的治理層補丁，沒有要求立即修改已實作模組。

但它會影響後續開工順序：

```text
原本 MVP2B_STATUS.md 的 next step:
  Proceed to MVP2C

v8.2 修正後的治理決策:
  MVP2B acceptance
  → HARDEN-1: Extraction & Evidence / Figure Metadata Quality
  → MVP2C-thin
  → HARDEN-3: Media Quality / Composition
  → MVP2C-full or MVP3（於 HARDEN-3 後決定）
```

**路線延伸說明**：MVP2C-thin 之後不是開放式結尾。完成 thin 版本後，必須插入 HARDEN-3（TTS timing、subtitle readability、segment composition、audio loudness），再決定是否進入 full media generation 或直接推進至 MVP3 review committee。若不明確寫出這段，MVP2C-thin 完成後的「下一步模糊」壓力將重演 HARDEN-1 被跳過的同樣風險。

HARDEN-2（scene quality / presentation consistency / asset plan edge cases）的處置由 HARDEN-1 implementation plan 明確決定（見 N-004）。

這不是對 MVP2B 程式碼的否定，而是對專案節奏的修正。MVP2B 的完成狀態仍然有效；只是下一個 sprint 不應直接開 full MVP2C。

---

## 4. 實作時的注意事項

### N-001｜HARDEN-1 需要獨立 implementation plan

v8.2 只定義 hardening governance，不展開 HARDEN-1 的實作細節。接下來應建立獨立文件：

```text
IMPLEMENTATION_PLAN_HARDEN1_EXTRACTION_EVIDENCE.md
```

該文件再負責定義具體 deliverables，例如：

```text
- section detection hardening
- figure / table metadata baseline
- caption extraction
- evidence span normalization and matching calibration
- real-paper smoke set
- golden fixtures
- extraction_quality_report.json
```

### N-002｜MVP2C 應先做 thin version

v8.2 將 MVP2C 的下一步定位修正為 `MVP2C-thin`，不是 full media generation。`MVP2C-thin` 應優先建立最小可播放閉環，例如：

```text
asset_plan.json
→ Edge-TTS audio
→ text_card / static_background fallback visuals
→ minimal ffmpeg composition
→ final/output.mp4
```

複雜 image generation、VRM rendering、lip sync、ComfyUI / RunningHub、Playwright template polish 等不應在 thin version 中一次展開。

### N-003｜MVP complete 不等於 quality complete

後續 status 文件應避免只寫「MVP complete」造成誤解。建議在每個 MVP status 中分清：

```text
- Contract complete
- Current verification
- Known quality gaps
- Hardening backlog
- Recommended next step
```

此要求最容易在 sprint 最後一天被遺漏，因此下一份 `IMPLEMENTATION_PLAN_HARDEN1_EXTRACTION_EVIDENCE.md` 應加入「標準 status 模板」作為交付物，之後所有 MVP / HARDEN status 文件都依此格式撰寫。

建議模板：

```markdown
# <MVP or HARDEN> Status

Last updated: YYYY-MM-DD

## Contract complete
- 已完成的 artifact / schema / CLI / service contract

## Current verification
- focused tests
- full regression
- manual smoke

## Known quality gaps
- 已知尚未解決的資料品質、真實案例、邊界條件或 reviewer 校準缺口

## Hardening backlog
- 應在後續 HARDEN sprint 補的項目

## Recommended next step
- 下一步 sprint 或明確暫停點
```

### N-004｜HARDEN-2 不可被隱性吞掉

v8.2 的建議節奏表中，HARDEN-2 對應 scene quality、presentation consistency、asset plan edge cases 與 figure/asset selection quality。但目前專案已完成 MVP2A、MVP2A-2 與 MVP2B，且 MVP2B v4 implementation plan 已處理多個 asset plan edge cases。

因此，HARDEN-1 implementation plan 必須明確決定 HARDEN-2 的狀態：

```text
- 合併進 HARDEN-1 的部分檢查
- 推遲到 MVP2C-thin 後另開 IMPLEMENTATION_PLAN_HARDEN2_SCENE_ASSET_QUALITY.md
- 或確認 MVP2B v4 implementation plan 的 edge case 修正已足夠覆蓋，正式標記為 superseded
```

若不做此決策，HARDEN-2 很可能被 HARDEN-1 與 MVP2C-thin 的壓力擠掉，導致未來無法回答「scene quality 是否曾被正式 harden」。

**執行保障**：為確保這個決策不因撰寫者未讀 migration log 而遺失，HARDEN-1 的 acceptance criteria 必須包含以下項目：

```text
[ ] HARDEN-2 狀態已明確決定，並以下列其中一種方式記錄：
    - 寫在 HARDEN-1_STATUS.md 的「Recommended next step」中，或
    - 獨立建立 IMPLEMENTATION_PLAN_HARDEN2_SCENE_ASSET_QUALITY.md，或
    - 在 HARDEN-1_STATUS.md 中標記 HARDEN-2 為 superseded 並說明理由。
未完成此項，HARDEN-1 不得標記為 accepted。
```

---

## 5. 共存期間規則

v8.2 是 v8.1 的純增量治理補丁，不需要長期共存期。

- **v8.1 直接被 v8.2 取代**，不保留 v8.1 作為平行現行版本。
- v8.1 的原始檔案移入 `docs/archive/architecture/v8.1/`，連同本 migration log 一起存放。
- `docs/current/` 應只保留 `P2S_redesign_architecture_v8.2.md` 作為唯一有效 Architecture Spec。

---

## 6. 歸檔計畫

```text
docs/archive/architecture/
  v8/
    P2S_redesign_architecture_v8.md
    MIGRATION_architecture_v8_to_v8.1.md
  v8.1/
    P2S_redesign_architecture_v8.1.md          ← v8.1 原始檔，不修改
    MIGRATION_architecture_v8.1_to_v8.2.md     ← 本文件
```

歸檔後：

```text
docs/current/
  P2S_redesign_architecture_v8.2.md             ← 唯一現行 Architecture Spec
```

---

## 7. 升版後的下一步

v8.2 生效後，建議下一個實作文件為：

```text
IMPLEMENTATION_PLAN_HARDEN1_EXTRACTION_EVIDENCE.md
```

而不是直接開：

```text
IMPLEMENTATION_PLAN_MVP2C_FULL_MEDIA_GENERATION.md
```

理由：MVP2B 已經建立 `asset_plan.json` contract，但 manual real-paper smoke 顯示目前上游缺少 figure metadata。若不先 harden extraction / evidence / figure metadata，MVP2C 會把上游資料品質問題放大成媒體生成問題。
