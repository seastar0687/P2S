# Migration Log：Architecture Spec v8 → v8.1

> 這份文件是 v8 → v8.1 升版的完整記錄。  
> 任何人（或 agentic AI）只需要讀這一份，就能知道：發生了什麼、改了什麼、有沒有衝突。

---

## 1. 升版時機與原因

- **時間**：2026-05-08，MVP2A 開工前的 hardening pass
- **觸發文件**：`IMPLEMENTATION_NOTE_CODE_VERSION_METADATA.md`
- **原因**：MVP0–MVP2A 的生成 artifact（`claims.json`、`scenes.json`、`presentation_plan.json` 等）存放在 `runs/` 目錄，刻意不納入 Git。但缺少「這個 artifact 是哪個 commit 產生的」的溯源資訊。v8.1 補入輕量的 code version provenance metadata，讓每個 stage 的輸出都可以追回對應的程式版本。

---

## 2. v8.1 相對於 v8 的變更內容

### 新增（純新增，無 breaking change）

| 項目 | 說明 |
|---|---|
| `5.5 Code Version Metadata` 章節 | Architecture Spec 新增完整的 CodeVersion 設計說明 |
| `CodeVersion` schema | `commit / branch / dirty / captured_at / source` |
| `ProjectState.code_version: CodeVersion \| None` | 頂層記錄最近一次 save 時的程式版本 |
| `StageState.code_version: CodeVersion \| None` | 每個 stage 記錄執行當下的程式版本 |
| `p2s_core/services/code_version.py` | `capture_code_version()` helper，git unavailable 時不 crash |
| `docs/current/` 引用更新 | `v8` → `v8.1` |

### 無 Breaking Change

v8.1 的所有新增欄位均為 `Optional`（`= None`）。舊的 `project_state.json` 不包含這些欄位時，Pydantic 會使用預設值，不會拋錯。**不需要修改任何現有測試。**

---

## 3. 與已實作程式碼的衝突

**無衝突。** v8.1 是純新增，向後相容。

MVP0（45 tests）、MVP1（69 tests）、MVP2A 的現有測試全部不受影響。

---

## 4. 實作時的注意事項

這些不是衝突，但實作者開工前值得知道：

**N-001｜`commit` 統一用 short hash（7 chars）**

Architecture Spec v8.1 的 CLI 範例（`05989ff main clean`）用 short hash，但 3.1 節說「short or full, be consistent」。建議統一用 `git rev-parse --short HEAD`（7 chars），status display 較整齊。

**N-002｜T2 測試在 detached HEAD 環境需要容錯**

CI 環境的 shallow clone 可能讓 `git rev-parse --abbrev-ref HEAD` 回傳 `"HEAD"` 而非 branch name。`branch` 欄位在 detached HEAD 狀態下為 `"HEAD"` 或 `None` 都視為合法，T2 測試不應對此 fail。

---

## 5. 共存期間規則

v8.1 是 v8 的純增量補丁，不需要共存期。

- **v8 直接被 v8.1 取代**，不保留 v8 作為平行版本。
- v8 的原始檔案移入 `docs/archive/architecture/v8/`，連同本文件一起存放。

---

## 6. 歸檔計畫

```
docs/archive/architecture/
  v7/
    P2S_redesign_architecture_v7.md
    MIGRATION_v7_to_v8.md
  v8/
    P2S_redesign_architecture_v8.md      ← v8 原始檔，不修改
    MIGRATION_architecture_v8_to_v8.1.md ← 本文件
```

歸檔後 `P2S_redesign_architecture_v8.1.md` 成為唯一現行 Architecture Spec，存放於 `docs/current/`。
