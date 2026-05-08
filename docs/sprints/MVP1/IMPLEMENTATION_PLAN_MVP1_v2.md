# P2S Implementation Plan — MVP 1

> **這份文件是 MVP1 sprint contract，不是長期架構文件。**  
> MVP0 已完成並通過自動化與手動 smoke 驗證；MVP1 的目標是在不膨脹到 UI / media / full reviewer committee 的前提下，建立第一個可信 claim-grounding 閉環。

---

## 0. Sprint 目標（一句話版本）

**讓「`extracted_text.md` → `claims.json` → `claim_review.json`」這條 claim-grounded pipeline 跑通，並用嚴格 schema、evidence gate、golden tests 檢查輸出可信度。**

MVP1 不追求影片、不追求漂亮文案、不追求完整多代理審查。MVP1 只回答一件事：

> 給定一篇已完成 extraction 的論文，P2S 是否能抽出主要 claims，並為每個 claim 提供可檢查的 evidence span？

---

## 1. MVP1 與 MVP0 的邊界

### 1.1 MVP0 已完成的前置條件

MVP0 已完成：

```text
p2s init paper.pdf
→ project_state.json
→ persona/style loader
→ p2s run --stage extraction
→ extracted_text.md
→ p2s status
```

MVP1 直接依賴 MVP0 的輸出：

```text
runs/{project_id}/extracted_text.md
runs/{project_id}/project_state.json
```

MVP1 不重新設計 MVP0 的 CLI / config / schema / persistence；只在其上擴充新的 stage。

### 1.2 MVP1 新增主線

```text
extracted_text.md
→ paper section chunking
→ claim extraction
→ evidence span selection
→ claim validation
→ claim review
→ claims.json + claim_review.json
```

### 1.3 MVP1 不做的事

```text
✗ Streamlit UI
✗ full script generation
✗ storyboard generation
✗ TTS / image / video generation
✗ full multi-agent review committee
✗ final video review
✗ persona acquisition
✗ voice cloning / VRM
✗ online deployment / user study
✗ automatic paper figure extraction beyond MVP0 plain text
```

若某功能無法直接服務於 `claims.json` 與 `claim_review.json`，本 sprint 不做。

---

## 2. MVP1 分級標準

MVP1 採三層分級，避免功能膨脹。

### 2.1 Must：必做，否則 MVP1 不算完成

```text
M1. 新增 claim_extraction stage
M2. 建立 PaperSection / PaperChunk / ClaimExtractionResult schema
M3. LLMService 支援 structured output retry
M4. claim_extraction.py 能從 extracted_text.md 產生 claims.json
M5. 每個 claim 必須有至少一個 EvidenceSpan
M6. ClaimEvidenceReviewer v1 能檢查 claim 是否有 evidence
M7. PaperFidelityReviewer v1 能檢查明顯 unsupported / overhyped claim
M8. Arbiter v1 能輸出 GateDecision
M9. CLI 支援 `p2s run --stage claim_extraction`
M10. 測試：schema、LLM fake client、claim extraction fake pipeline、review gate、golden bad cases
```

### 2.2 Should：建議做，但可延後一週

```text
S1. section detection v1：Abstract / Introduction / Method / Result / Limitation / Conclusion 粗分段
S2. chunking strategy：依 section + token budget 切塊（預設 max_tokens_per_chunk = 800；可在 config.yaml extraction.chunk_max_tokens 覆蓋）
S3. claim importance scoring 1-5
S4. claim type distribution check：至少包含 contribution / method / result / limitation 的候選
S5. extraction quality report：文字長度、section 覆蓋、claim 數量、evidence 覆蓋率
S6. `p2s inspect claims --project <id>` 純 CLI 顯示 claims table
```

### 2.3 Deferred：明確延後，不准偷做

```text
D1. Streamlit Claim Table UI
D2. scene/script generation
D3. reviewer auto-fix loop
D4. multi-round debate
D5. visual planning
D6. citation overlay / video evidence view
D7. model comparison benchmark
D8. full RQ1 experiment
```

---

## 3. 新增檔案結構

在 MVP0 基礎上新增：

```text
p2s_core/
  models/
    paper.py                         # PaperSection, PaperChunk, ExtractedPaper
    extraction_result.py             # ClaimExtractionResult, ClaimReviewBundle
  services/
    text_chunking.py                 # section / chunking utility
    claim_extraction.py              # LLM-based claim extraction
  reviewers/
    __init__.py
    base.py                          # BaseReviewer
    claim_evidence.py                # ClaimEvidenceReviewer v1
    paper_fidelity.py                # PaperFidelityReviewer v1
    arbiter.py                       # Arbiter v1
    # devil_advocate.py              # ← Deferred（MVP3），本 sprint 不建立此檔案
  prompts/
    claim_extraction_v1.md
    review/
      claim_evidence_v1.md
      paper_fidelity_v1.md
      arbiter_v1.md
  tests/
    golden/
      paper_toy_001/
        extracted_text.md
        expected_claims_minimal.json
      bad_claims/
        unsupported_claim_001.json
        overhyped_claim_001.json
        missing_evidence_001.json
    test_text_chunking.py
    test_claim_extraction_schema.py
    test_claim_extraction_fake.py
    test_claim_reviewers.py
    test_claim_stage_smoke.py
```

輸出目錄新增：

```text
runs/{project_id}/
  claims.json
  reviews/
    claim_review_rev001.json         ← ClaimReviewBundle（含 reviews list + gate_decision）
```

> **落盤原則**：`ClaimReviewBundle` 以單一 JSON 檔案落盤，`gate_decision` 內嵌其中，不另外拆出獨立檔案。`project_state.reviews` 同步寫入所有 `ReviewResult`，`project_state.stages.claim_extraction` 記錄最終 gate status。

> **Schema ownership 原則**：`EvidenceSpan` 繼續沿用 MVP0 的 `models/common.py`，不要在 `paper.py` 重複定義。`PaperClaim` 繼續放在 `models/claim.py`，不要搬到 `paper.py`。MVP1 新增的 `models/paper.py` 只放 `PaperSection`、`PaperChunk`、`ExtractedPaper`；`models/extraction_result.py` 只放 `ClaimExtractionResult`、`ClaimReviewBundle`。

---

## 4. Schema 規格

### 4.1 PaperSection

```python
class PaperSection(BaseModel):
    section_id: str
    title: str
    section_type: Literal[
        "abstract", "introduction", "background", "method",
        "experiment", "result", "discussion", "limitation",
        "conclusion", "unknown"
    ] = "unknown"
    text: str
    start_char: int | None = None
    end_char: int | None = None
    page_start: int | None = None
    page_end: int | None = None
```

### 4.2 PaperChunk

```python
class PaperChunk(BaseModel):
    chunk_id: str
    section_id: str
    section_type: str
    text: str
    char_start: int | None = None
    char_end: int | None = None
    token_estimate: int | None = None
```

### 4.3 EvidenceSpan（沿用 MVP0，但 MVP1 要求更嚴格）

```python
class EvidenceSpan(BaseModel):
    section: str
    text: str
    page: int | None = None
    confidence: Literal["direct", "inferred", "weak"] = "direct"
```

MVP1 hard rule：

```text
- claims.json 只保存 accepted schema-valid claims。
- accepted claims 中每個 PaperClaim 至少 1 個 EvidenceSpan。
- EvidenceSpan.text 不得為空。
- EvidenceSpan.confidence == "weak" 的 claim 不能直接 pass gate，必須標記 needs_review。
- 無 evidence 的候選 claim 不進入 claims.json；必須寫入 quality_report.invalid_candidates。
```

### 4.4 PaperClaim（MVP1 強化）

```python
class PaperClaim(BaseModel):
    claim_id: str
    claim_text: str
    claim_type: Literal[
        "problem", "method", "result", "limitation",
        "contribution", "background"
    ]
    source_section: str
    evidence_spans: list[EvidenceSpan]
    certainty: Literal["explicit", "inferred", "weak"]
    importance: int  # 1-5
    risk_flags: list[Literal[
        "unsupported", "overhyped", "missing_evidence",
        "weak_evidence", "ambiguous", "too_broad"
    ]] = []
```

### 4.5 ClaimExtractionResult

```python
class ClaimExtractionResult(BaseModel):
    project_id: str
    claims: list[PaperClaim]              # accepted schema-valid claims only
    source_chunk_ids: list[str]           # 記錄本次抽取使用過的 PaperChunk.chunk_id
    extraction_model: str | None = None
    prompt_version: str = "claim_extraction_v1"
    created_at: str
    quality_report: dict = {}
```

`quality_report` 至少要能容納無法進入 `claims.json` 的候選 claim：

```json
{
  "invalid_candidates": [
    {
      "claim_text": "...",
      "reason": "missing_evidence",
      "source_chunk_id": "chunk_003"
    }
  ]
}
```

> **注意**：不要把完整 `PaperChunk` 物件塞進 `ClaimExtractionResult`。完整 chunk 資料由 chunking stage / 中間檔管理；結果檔只保存 `source_chunk_ids` 以維持可追蹤性。

### 4.6 ClaimReviewBundle

```python
class ClaimReviewBundle(BaseModel):
    project_id: str
    target_stage: Literal["claim_extraction"] = "claim_extraction"
    reviews: list[ReviewResult]
    gate_decision: GateDecision
    created_at: str
```

---

## 5. Stage 設計

### 5.1 新增 stage：claim_extraction

CLI：

```bash
p2s run --stage claim_extraction --project <project_id>
```

前置條件：

```text
stages.extraction.status == done
extracted_text.md exists and non-empty
```

執行步驟：

```text
1. load project_state.json
2. read extracted_text.md
3. text_chunking.py 建立 PaperSection / PaperChunk
4. claim_extraction.py 呼叫 LLMService 產生 ClaimExtractionResult
5. schema validation：只允許 accepted schema-valid claims 進入 `claims.json`
6. 將無 evidence / schema invalid 的候選 claim 寫入 `quality_report.invalid_candidates`
7. write claims.json
8. run ClaimEvidenceReviewer v1
9. run PaperFidelityReviewer v1
10. Arbiter v1 產生 GateDecision
11. write reviews/claim_review_rev001.json
12. 更新 project_state.claims / reviews / stages.claim_extraction
```

### 5.2 claim_extraction stage status rule

```text
pass gate:
  → stages.claim_extraction.status = done

human_check gate:
  → stages.claim_extraction.status = needs_review

reject gate:
  → stages.claim_extraction.status = failed 或 rejected
  → 若是 LLM/API/schema error: failed
  → 若是 factuality gate fail: rejected
```

### 5.3 不做 auto-fix loop

MVP1 不做自動修正循環。若 reviewer fail：

```text
- 記錄問題
- 標記 needs_review / rejected
- 不自動重生
```

自動修正循環留到 MVP3。

---

## 6. Reviewer v1 嚴格規格

### 6.1 ClaimEvidenceReviewer v1

目的：檢查每個 claim 是否至少形式上有 evidence。

MVP1 v1 先採 deterministic + optional LLM hybrid。

必做 deterministic checks：

```text
1. evidence_spans 非空
2. evidence_span.text 非空
3. evidence_span.text 至少 30 字或 8 個英文詞以上
4. evidence_span.text 必須出現在 extracted_text.md 中，或 fuzzy match ratio >= 0.85
5. confidence == weak → pass_gate = false, severity >= medium
```

Fuzzy matching 規格：

```text
- MVP1 使用 Python 標準庫 difflib.SequenceMatcher，不新增 heavy dependency。
- 不直接拿 evidence_text 對整篇 extracted_text 計算 ratio。
- 最低可用實作：
  1. 若 evidence_text in extracted_text → pass
  2. 否則將 extracted_text 依空行切成 paragraph
  3. 對每個 paragraph 計算 SequenceMatcher ratio
  4. max_ratio >= 0.85 → pass
  5. 否則 high fail
```

輸出：

```python
ReviewResult(
    target_type="claim",
    target_id=claim.claim_id,
    reviewer="ClaimEvidenceReviewer",
    score=0.0-1.0,
    pass_gate=bool,
    severity="low|medium|high|critical",
    findings=[...],
    suggested_fixes=[...],
)
```

Hard fail：

```text
- evidence_spans = [] → critical fail
- evidence text 不存在於 extracted_text.md 且 fuzzy < 0.85 → high fail
```

### 6.2 PaperFidelityReviewer v1

目的：抓明顯 unsupported / overhyped / too broad claim。

MVP1 v1 最小版：rule-based + LLM judge optional。

Rule-based checks：

```text
Forbidden hype terms:
- 證明
- 完全解決
- 革命性
- 顛覆
- guarantee
- proves
- revolutionizes
- completely solves

If claim contains hype term and evidence does not contain equivalent wording:
→ severity >= high
→ pass_gate = false
```

Additional checks：

```text
- claim_type == result but no numeric / comparative / experimental evidence → medium warning
- claim_type == limitation but source_section not limitation/discussion/conclusion → low/medium warning
- certainty == weak and importance >= 4 → high warning
```

### 6.3 DevilAdvocate v1：Deferred

MVP1 **不建立** `devil_advocate.py`。此 reviewer 列入 MVP3 範圍，屆時實作 rule-based overhype check 或 LLM debate。本 sprint 不建立任何 DevilAdvocate 相關檔案或 stub。

### 6.4 Arbiter v1

輸入：ClaimEvidenceReviewer + PaperFidelityReviewer 的 ReviewResult list。

MVP1 將 gate 分成兩層：**claim-level decision** 與 **artifact-level decision**。這樣一個壞 claim 不會讓整個 stage 失去診斷價值，但也不會把壞 claim 混進 accepted claims 裡。

Claim-level decision：

```text
1. critical fail → 該 claim rejected
2. high fail → 該 claim needs_review
3. medium fail → 該 claim warning
4. 無 fail → 該 claim pass
```

Artifact-level GateDecision：

```text
1. rejected_claim_ratio > 0.30 → status = reject
2. 任一 high fail / weak evidence / needs_review claim → status = human_check
3. medium fail 數量 >= 3 → status = human_check
4. 否則 status = pass
```

MVP1 不做 revise，因為不做 auto-fix。

```python
status: Literal["pass", "human_check", "reject"]
```

注意：長期 GateDecision schema 仍可保留 `revise`，但 MVP1 Arbiter 不輸出 revise。

---

## 7. LLMService MVP1 擴充

MVP0 LLMService 只需 health check。MVP1 必須加入：

```text
- structured output with Pydantic response_type
- JSON extraction fallback
- max_retries
- fake client injection for tests
- raw response logging on parse failure
```

### 7.1 complete() 規格

```python
async def complete(
    self,
    messages: list[dict],
    response_type: type[BaseModel] | None = None,
    temperature: float = 0.2,
    max_retries: int = 3,
    retry_delay_sec: float = 1.0,
) -> BaseModel | str:
    ...
```

### 7.2 Structured output fallback order

```text
1. Try direct JSON parse
2. Try ```json ... ``` block
3. Try first {...} object extraction
4. Pydantic model_validate
5. On failure, retry with stricter instruction
6. After max_retries, write raw response to runs/{project_id}/debug/llm_raw_*.txt
```

---

## 8. Claim extraction prompt 嚴格要求

Prompt 必須要求：

```text
- 不要寫短影音腳本
- 不要改寫成口語文案
- 只抽取論文主張
- 每個 claim 必須有 evidence span
- evidence span 必須盡量直接引用原文
- limitation 必須保留，如果論文有相關內容
- 不確定時標記 certainty = weak，不要硬說
```

Prompt output schema：`ClaimExtractionResult`。

Claim 數量限制：

```text
minimum: 5 claims
maximum: 15 claims
ideal: 8-12 claims
```

Claim type target：

```text
- 至少 1 個 problem/background
- 至少 1 個 method/contribution
- 至少 1 個 result（若論文有實驗）
- 至少 1 個 limitation/discussion（若論文有）
```

若不足，quality_report 記錄：

```json
{
  "missing_claim_types": ["limitation"],
  "reason": "No explicit limitation section detected"
}
```

---

## 9. 測試與驗收分級

### 9.1 Test Tier 0：單元測試，必須全過

```text
test_text_chunking.py
  ✓ extracted_text → chunks
  ✓ empty text raises clear error
  ✓ chunk token estimate below limit

test_claim_extraction_schema.py
  ✓ ClaimExtractionResult roundtrip
  ✓ ClaimExtractionResult 使用 source_chunk_ids，不嵌入完整 PaperChunk
  ✓ PaperClaim requires evidence
  ✓ weak evidence triggers validation warning or review fail

test_claim_reviewers.py
  ✓ missing evidence → ClaimEvidence critical fail
  ✓ fuzzy unmatched evidence → high fail
  ✓ overhyped claim → PaperFidelity high fail
  ✓ clean claim with direct evidence → pass

test_arbiter.py
  ✓ critical fail → reject
  ✓ rejected_claim_ratio > 0.30 → artifact reject
  ✓ high fail → human_check
  ✓ all pass → pass
```

### 9.2 Test Tier 1：Fake LLM pipeline，必須全過

使用 fake client，不呼叫真 API。

```text
test_claim_extraction_fake.py
  ✓ fake LLM returns valid claims
  ✓ malformed JSON retry succeeds
  ✓ malformed JSON after max retry writes debug raw file
  ✓ claims.json written
  ✓ missing-evidence candidate 寫入 quality_report.invalid_candidates，而非 claims.json
```

### 9.3 Test Tier 2：Golden bad cases，必須全過

每個 golden bad case 是一個獨立的 `PaperClaim` JSON 物件，直接 feed 進對應 reviewer（不需要完整 `ClaimExtractionResult`）。格式示意：

```json
{
  "claim_id": "bad-001",
  "claim_text": "...",
  "claim_type": "result",
  "source_section": "abstract",
  "evidence_spans": [],
  "certainty": "explicit",
  "importance": 3,
  "risk_flags": []
}
```

```text
golden/bad_claims/missing_evidence_001.json
  → evidence_spans = []
  → ClaimEvidenceReviewer critical fail

golden/bad_claims/unsupported_claim_001.json
  → evidence_span.text 不存在於 extracted_text.md（fuzzy < 0.85）
  → ClaimEvidenceReviewer high fail

golden/bad_claims/overhyped_claim_001.json
  → claim_text 含 forbidden hype term（如 "proves" / "完全解決"）
  → PaperFidelityReviewer high fail
```

### 9.4 Test Tier 3：Manual real-paper smoke，至少 1 篇通過

手動測試：

```bash
p2s init paper.pdf
p2s run --stage extraction
p2s run --stage claim_extraction
p2s status
```

驗收輸出：

```text
✓ claims.json exists
✓ claims count between 5 and 15
✓ every claim has evidence_spans
✓ reviews/claim_review_rev001.json exists
✓ gate_decision exists
✓ stage status is done / needs_review / rejected，不能 crash
```

注意：真實 LLM smoke 不要求一定 pass gate，因為論文、模型、prompt 可能導致 needs_review。MVP1 要求的是「穩定產生可審查結果」，不是保證所有論文自動 pass。

---

## 10. Definition of Done

MVP1 完成需同時滿足：

```text
DoD-1: 所有 Tier 0 / Tier 1 / Tier 2 測試全過
DoD-2: 至少 1 篇真實 PDF 完成 extraction + claim_extraction stage，不 crash
DoD-3: claims.json schema 合法
DoD-4: claims.json 中每個 accepted claim 至少 1 個 evidence span；無 evidence 的候選 claim 必須記錄在 quality_report.invalid_candidates
DoD-5: claim_review_rev001.json schema 合法
DoD-6: `reviews/claim_review_rev001.json` 存在，schema 合法，`gate_decision` 內嵌於 `ClaimReviewBundle`
DoD-7: `p2s status` 能顯示 claim_extraction 狀態
DoD-8: README 或 MVP1_STATUS.md 更新目前完成狀態
```

MVP1 不以「claim 品質完美」為完成條件，而以「可檢查、可審查、可落盤、可失敗而不中斷」為完成條件。

---

## 11. 嚴格失敗條件

出現以下任一情況，MVP1 不算完成：

```text
F1. claims.json 的 accepted claims 中存在沒有 evidence_spans 的 claim
F2. stage failed 但沒有清楚 error message
F3. LLM malformed output 讓整個 CLI crash
F4. review result 沒有 target_id，無法定位問題 claim
F5. reviewer 只給總分，不給 findings / suggested_fixes
F6. `p2s status` 無法顯示 claim_extraction stage
F7. 測試依賴真 OpenAI API 才能通過
F8. 實作中偷偷加入 Streamlit / TTS / video 造成 scope 膨脹
```

---

## 12. 時程建議（10-12 天）

| 天數 | 任務 |
|---|---|
| Day 1 | 新增 paper.py / extraction_result.py schema + tests |
| Day 2 | text_chunking.py + section/chunk tests |
| Day 3 | LLMService structured output + fake client tests |
| Day 4 | claim_extraction.py fake pipeline，寫 claims.json |
| Day 5 | claim_extraction prompt v1 + raw debug logging |
| Day 6 | ClaimEvidenceReviewer v1 + tests |
| Day 7 | PaperFidelityReviewer v1 + Arbiter v1 + tests |
| Day 8 | CLI stage integration：run --stage claim_extraction / status |
| Day 9 | golden bad cases + review bundle output |
| Day 10 | manual real-paper smoke |
| Day 11 | cleanup / docs / MVP1_STATUS.md |
| Day 12 | buffer |

警示信號：

```text
- Day 3 還在做 provider switching → 砍掉，只支援 OpenAI + fake client
- Day 5 想開始 script generation → 停止，MVP1 不做
- Day 7 想做 multi-agent debate → 停止，只做 deterministic / simple reviewer
- Day 8 還沒有 claims.json 落盤 → 優先完成落盤，不要優化 prompt
```

---

## 13. MVP1 完成後的下一步

MVP1 完成後，才進入 MVP2 / Research Phase A 的下一段：

```text
claims.json
→ SceneDraft generation
→ script_fidelity review
→ human-editable script artifacts
```

這可以命名為：

```text
MVP2A: Claim-grounded script generation
```

不要直接跳到影片生成。影片生成應等 script + review 穩定後再進入。

---

## 14. 給實作者的提醒

1. **MVP1 的主角是 claims，不是 script。**
2. **Evidence span 是 hard requirement，不是附加欄位。**
3. **LLM 失敗是正常路徑，不能讓 CLI crash。**
4. **Reviewer v1 寧可簡單嚴格，不要複雜玄學。**
5. **所有輸出都要落盤，所有失敗都要可診斷。**
6. **不要做 UI，不要做影片，不要做完整多代理辯論。**

