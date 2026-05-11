# IMPLEMENTATION PLAN — P2S HARDEN-1：Extraction & Evidence / Figure Metadata Quality

> 文件定位：本文件是 **HARDEN-1 sprint contract**，可直接交給 coding agent / Codex / Claude Code 作為開工依據。  
> 本階段不是新增下游功能，而是回補 MVP0–MVP2B 已累積的上游資料品質債。  
> **HARDEN-1 只做 extraction / evidence / figure metadata / real-paper calibration hardening，不做媒體生成。**

---

## 0. 背景與當前前提

目前 P2S 已完成：

```text
MVP0   → schema / state / CLI / basic extraction
MVP1   → claim extraction / evidence mapping / deterministic reviewers
MVP2A  → narrative planning / presentation planning
MVP2A-2→ LLM quality rewrite / active_scene_source
MVP2B  → asset_preparation / asset_plan.json
```

MVP2B manual real-paper smoke 已證明 `asset_plan.json` contract 可以建立，但也暴露出上游缺口：

```text
Warning:
No figure metadata found; paper_figure selection will use fallback behavior.
```

因此，依照 Architecture Spec v8.2 的治理節奏，下一步不應直接進 full MVP2C，而應先插入：

```text
HARDEN-1: Extraction & Evidence / Figure Metadata Quality
```

HARDEN-1 的目標不是「讓 extraction 完美」，而是讓進入 MVP2C-thin 前的上游資料具備最低可用品質：

```text
PDF
→ extracted_text.md
→ extraction_quality_report.json
→ figures.json / figures metadata
→ claims.json
→ claim_review
→ asset_plan.json re-smoke
```

---

## 1. HARDEN-1 核心目標

HARDEN-1 的核心目標是降低下游 media generation 放大上游錯誤的風險。

具體而言，本 sprint 要改善四件事：

```text
1. PDF text extraction quality
   - section detection 更穩定
   - line break / hyphenation / spacing normalization 更可靠
   - extraction_quality_report.json 可見化品質缺口

2. Figure / table metadata baseline
   - 至少建立可用的 figure metadata contract
   - 支援 figure_id / page / bbox / caption / image_path / confidence
   - 讓 MVP2B paper_figure selection 不再只能無條件 fallback

3. Evidence matching calibration
   - 把 MVP1 已有的 normalization / fuzzy matching 收斂成可測試 contract
   - 減少 evidence false positive / false negative
   - 建立 golden fixtures

4. Real-paper smoke set
   - 不再只靠一篇 mvp1_real_smoke
   - 至少加入 2–3 篇不同 layout 的 real-paper smoke
   - 記錄每篇的 extraction / claim / asset_plan quality summary
```

完成後，HARDEN-1 應該讓下一階段 MVP2C-thin 可以更安全地接：

```text
asset_plan.json
→ Edge-TTS audio
→ text_card / static_background / selected paper figure fallback
→ minimal ffmpeg composition
```

---

## 2. Non-goals：HARDEN-1 明確不做

HARDEN-1 不是 MVP2C，也不是 full extraction research project。

禁止在本 sprint 中實作：

```text
- 真實 TTS generation
- image generation
- VRM rendering
- lip sync / motion generation
- Playwright HTML frame rendering
- ffmpeg video composition
- Streamlit UI
- full OCR pipeline for all scanned PDFs
- full table structure extraction
- LLM-backed paper layout understanding
- LLM-backed visual planning rewrite
- new reviewer committee / auto-fix loop
```

允許但應保持低風險：

```text
- PyMuPDF-based figure image extraction
- deterministic caption matching
- deterministic section detection hardening
- deterministic quality report
- golden fixture organization
- real-paper smoke scripts
- compatibility / migration patches for old project runs
```

---

## 3. HARDEN-2 處置決策

Architecture v8.2 要求 HARDEN-1 必須明確處理 HARDEN-2 的狀態，避免 scene quality / presentation consistency / asset plan quality 被隱性吞掉。

本文件採用以下決策：

```text
HARDEN-2 is NOT superseded.
HARDEN-2 is partially touched by HARDEN-1 only where it depends on upstream extraction quality.
A separate HARDEN-2 plan stub must be created before HARDEN-1 can be accepted.
```

也就是：

```text
HARDEN-1 會做：
- figure metadata 是否足以支援 asset_plan 的 paper_figure selection
- asset_plan 在新 real-paper smoke set 上是否還出現 missing figure metadata warning
- presentation / asset plan 是否因 extraction 缺口而退化

HARDEN-1 不會完整做：
- scene wording quality
- presentation consistency deep review
- asset plan aesthetic quality
- visual plan / scene intent semantic quality
```

HARDEN-1 acceptance criteria 必須包含：

```text
[ ] 已建立 IMPLEMENTATION_PLAN_HARDEN2_SCENE_ASSET_QUALITY.md stub
    或在 HARDEN1_STATUS.md 中明確說明 HARDEN-2 的後續處置。
```

**建議路線（與 Architecture v8.2 Section 10A.4 一致）：**

```text
HARDEN-1
→ MVP2C-thin
→ HARDEN-3: Media Quality / Composition（mandatory，不可跳過）
→ HARDEN-2 於此時以「scene/media mismatch」為具體檢查基礎重新評估
```

說明：HARDEN-3 在 MVP2C-thin 後是強制插入點，不是 decision point。HARDEN-2 的深度 scene quality 檢查可在此時結合 media 輸出做更有依據的驗證，但這不代表 HARDEN-2 可以被無限期推遲——其 stub 必須在 HARDEN-1 完成前建立。

---

## 4. 新增 / 修改檔案清單

### 4.1 Models

新增或擴充：

```text
p2s_core/models/extraction.py
p2s_core/models/figure.py
p2s_core/models/quality.py
```

若目前已有 paper/extraction models，可選擇整合到既有檔案，但需保持清楚邊界。

建議新增 schema：

```text
ExtractedSection
ExtractedFigure
ExtractedTable
ExtractionQualityReport
EvidenceMatchReport
RealPaperSmokeReport
```

### 4.2 Services

修改 / 新增：

```text
p2s_core/services/paper_extraction.py
p2s_core/services/figure_extraction.py
p2s_core/services/evidence_matching.py
p2s_core/services/extraction_quality.py
p2s_core/services/text_normalization.py
```

若目前 evidence matching 邏輯在 reviewer 內部，HARDEN-1 應抽出共用 helper，避免 reviewer / tests / diagnostics 各寫一套 normalization。

### 4.3 Reviewers / Validators

修改：

```text
p2s_core/reviewers/claim_evidence.py
p2s_core/reviewers/paper_fidelity.py
```

新增或抽出：

```text
p2s_core/reviewers/evidence_match_validator.py
```

### 4.4 CLI / Pipeline

新增或擴充 CLI：

```bash
python -m p2s_core.cli run --stage extraction --project <project_id> --force
python -m p2s_core.cli run --stage claim_extraction --project <project_id> --force
python -m p2s_core.cli harden extraction --project <project_id>
python -m p2s_core.cli smoke real-papers --set harden1
```

若不想新增 `harden` / `smoke` command，至少應提供可被 pytest 或 script 呼叫的 smoke runner。

### 4.5 Tests

新增：

```text
tests/test_extraction_quality_schema.py
tests/test_text_normalization.py
tests/test_section_detection_hardening.py
tests/test_figure_extraction_metadata.py
tests/test_caption_matching.py
tests/test_evidence_matching_hardening.py
tests/test_harden1_pipeline_integration.py
tests/test_harden1_real_smoke_runner.py
```

擴充：

```text
tests/test_claim_evidence_reviewer.py
tests/test_asset_preparation_service.py
```

### 4.6 Fixtures / Golden Data

新增：

```text
tests/fixtures/papers/harden1/
  simple_two_column.pdf
  figure_caption_sample.pdf
  messy_linebreak_sample.pdf
  no_figure_sample.pdf

tests/golden/extraction/
  simple_two_column_expected_sections.json
  figure_caption_expected_figures.json
  messy_linebreak_expected_normalized_text.json

tests/golden/evidence/
  evidence_match_good_cases.json
  evidence_match_bad_cases.json
  evidence_match_linebreak_cases.json
  evidence_match_hyphenation_cases.json
```

若無法在 repo 內放真實 PDF，則使用 synthetic PDF fixtures 或 small public-domain/generated PDFs。

### 4.7 Docs

新增：

```text
docs/sprints/HARDEN1/IMPLEMENTATION_PLAN_HARDEN1_EXTRACTION_EVIDENCE.md
docs/sprints/HARDEN1/HARDEN1_STATUS.md
docs/sprints/HARDEN2/IMPLEMENTATION_PLAN_HARDEN2_SCENE_ASSET_QUALITY.md  # stub
```

---

## 5. Schema 設計

### 5.1 ExtractedSection

```python
class ExtractedSection(BaseModel):
    section_id: str
    title: str
    normalized_title: str
    level: int | None = None
    page_start: int | None = None
    page_end: int | None = None
    text: str
    char_start: int | None = None
    char_end: int | None = None
    confidence: Literal["high", "medium", "low"] = "medium"
    detection_method: str = "regex"
    warnings: list[str] = []
```

最低要求：

```text
- section_id deterministic，例如 section_001
- title 不得為空
- normalized_title 用於 matching，例如 abstract / introduction / methods / results
- confidence 反映 detection certainty
```

---

### 5.2 ExtractedFigure

```python
class ExtractedFigure(BaseModel):
    figure_id: str
    page: int | None = None
    image_path: str | None = None
    caption: str | None = None
    caption_source: Literal["direct", "nearby_text", "inferred", "missing"] = "missing"
    bbox: list[float] | None = None
    width: float | None = None
    height: float | None = None
    confidence: Literal["high", "medium", "low"] = "low"
    extraction_method: str = "pymupdf"
    risk_flags: list[str] = []
    notes: str | None = None
```

最低要求：

```text
- 如果抽到圖片但沒 caption，仍保留 figure metadata，caption_source="missing"。
- 如果 caption 存在但圖片未成功抽出，也可保留 metadata，image_path=None 並 warning。
- figure_id 必須穩定，例如 fig_001。
```

---

### 5.3 ExtractedTable

```python
class ExtractedTable(BaseModel):
    table_id: str
    page: int | None = None
    image_path: str | None = None
    caption: str | None = None
    caption_source: Literal["direct", "nearby_text", "inferred", "missing"] = "missing"
    extraction_method: str = "pymupdf_image"
    confidence: Literal["high", "medium", "low"] = "low"
    notes: str | None = None
```

HARDEN-1 不做 full table structure extraction；table 先以 image + caption metadata 為主。

---

### 5.4 ExtractionQualityReport

```python
class ExtractionQualityReport(BaseModel):
    project_id: str
    text_char_count: int
    page_count: int | None = None

    section_count: int
    detected_section_titles: list[str]
    missing_expected_sections: list[str]

    figure_count: int
    figures_with_caption_count: int
    figures_without_caption_count: int

    table_count: int
    tables_with_caption_count: int
    tables_without_caption_count: int

    normalization_applied: list[str] = []
    warnings: list[str] = []
    quality_level: Literal["good", "acceptable", "poor", "failed"]
    created_at: str
```

Quality level 初版規則：

```text
failed:
  - text_char_count < 500
  - or extraction crashed
  - or source.pdf unreadable

poor:
  - no abstract/introduction-like section
  - or text_char_count unexpectedly short
  - or severe encoding corruption

acceptable:
  - text exists
  - claims can likely be extracted
  - section detection may be incomplete
  - figure metadata may be partial

good:
  - text length reasonable
  - at least abstract/introduction-like section detected
  - figures/captions extracted when present
```

HARDEN-1 不應過度 fail；除非 extraction 完全不可用，否則多數問題應成為 warning。

---

### 5.5 EvidenceMatchReport

```python
class EvidenceMatchReport(BaseModel):
    claim_id: str
    evidence_text: str
    matched: bool
    match_score: float
    match_method: Literal[
        "exact",
        "normalized_exact",
        "fuzzy",
        "short_quote",
        "not_found",
    ]
    matched_section: str | None = None
    matched_page: int | None = None
    warnings: list[str] = []
```

目的：

```text
- 讓 evidence matching 不只是 reviewer 裡的一個 boolean。
- 方便測 false positive / false negative。
- 讓 real-paper smoke 能統計 evidence matching quality。
```

---

### 5.6 RealPaperSmokeReport

```python
class RealPaperSmokeReport(BaseModel):
    project_id: str
    paper_name: str
    stages_run: list[str]
    extraction_quality: ExtractionQualityReport
    claim_count: int
    failed_claim_review_count: int
    asset_plan_warning_count: int
    key_warnings: list[str] = []
    passed: bool
    notes: str | None = None
    created_at: str
```

---

## 6. HARDEN-1 實作範圍

### 6.1 Text normalization hardening

建立共用 normalization helper：

```text
p2s_core/services/text_normalization.py
```

最低功能：

```text
- normalize Unicode spacing
- remove repeated whitespace
- merge PDF line-break artifacts
- fix hyphenated line breaks, e.g. "trans-\nformer" → "transformer"
- normalize ligatures, e.g. ﬁ → fi
- preserve paragraph boundaries where possible
```

輸出建議：

```text
runs/{project_id}/extracted_text.md            ← 原始版本，永遠保留
runs/{project_id}/extracted_text_normalized.md ← optional，若產出則供診斷用
```

> **重要**：`extracted_text_normalized.md` 是可選的輸出檔案，不是 evidence matching 的必要依賴。
> Evidence matching helper 必須能在此檔案不存在的情況下正常運作（見 Section 6.5）。
> 若產出，需在 `extraction_quality_report.json` 的 `normalization_applied` 欄位中記錄套用的步驟。

---

### 6.2 Section detection hardening

改善目前 section detection：

```text
- 支援 Abstract / Introduction / Related Work / Method / Methods / Experiments / Results / Discussion / Conclusion / Limitations
- 支援 numbered headings: 1 Introduction, 2.1 Method, III. Results
- 支援 uppercase headings
- 避免把 figure caption 誤判成 section
- 避免 repeated header/footer 被當成 section
```

輸出：

```text
runs/{project_id}/sections.json
project_state.extraction.sections_path = "sections.json"
```

最低要求：

```text
- 每篇 paper 至少產生 section list。
- 若無法可靠分段，也要建立 fallback single section：
  section_id="section_001", title="Full Text", confidence="low"
```

---

### 6.3 Figure metadata baseline

新增或強化 `figure_extraction.py`。

最低功能：

```text
- 從 PDF 抽取 image blocks，保存到 figures/
- 建立 figures.json
- 嘗試 caption matching
- caption matching 先 deterministic，不用 LLM
```

輸出：

```text
runs/{project_id}/figures/
  fig_001.png
  fig_002.png

runs/{project_id}/figures.json
project_state.extraction.figures_path = "figures.json"
```

Caption matching 初版規則：

```text
1. 搜尋同頁文字中 Figure / Fig. / 圖 / 表 等 caption prefix。
2. 優先取距離 image bbox 最近的 caption。
3. 若無 bbox-text proximity 能力，先用同頁 caption order matching。
4. 若找不到 caption，caption_source="missing"，warning。
```

Figure metadata 不要求完美，但必須讓 MVP2B 能讀到：

```text
figure_id / caption / page / image_path / confidence
```

---

### 6.4 Table metadata baseline

HARDEN-1 不做 full table parser，但至少支援：

```text
- 偵測 Table / 表 caption
- 若能截圖或抽 image block，保存 table image
- 建立 tables.json 或放入 project_state.extraction.tables_path
```

若表格 extraction 太不穩，允許只做 caption metadata：

```text
table_id / caption / page / image_path=None / confidence="low"
```

---

### 6.5 Evidence matching hardening

把 evidence matching 改成可測、可報告。

**Text source 優先序（重要）：**

```text
evidence matching helper 的輸入優先序：
1. extracted_text_normalized.md（若存在）
2. extracted_text.md（fallback）

helper 本身也會在內部套用 normalization，因此即使只有
extracted_text.md，matching 行為仍是確定的。
helper 不得因 extracted_text_normalized.md 不存在而 fail 或 warn。
```

最低要求：

```text
- claim evidence span 可以在 normalized extracted text 中被找到或 fuzzy matched。
- matching result 產生 EvidenceMatchReport。
- ClaimEvidenceReviewer 使用同一套 helper，不再自己私有實作。
```

Matching 方法順序：

```text
1. exact match
2. normalized exact match
3. fuzzy match for long spans
4. short quote matching for short spans
5. not_found
```

Hard fail / warning 策略：

```text
- exact / normalized_exact → pass
- fuzzy with high score → pass with note
- fuzzy with medium score → warning
- not_found → fail reviewer gate or needs_review, depending severity
```

---

### 6.6 Claim extraction smoke recalibration

HARDEN-1 不重寫 claim extraction prompt 為主要目標，但要校準：

```text
- 目前 claim type 是否過度集中 method
- 是否漏掉 limitation / result / contribution
- 是否 evidence spans 太長或太短
- 是否 evidence matching false fail
```

允許小幅 prompt patch：

```text
- encourage claim type diversity when paper supports it
- require limitations if explicitly present
- constrain evidence span length
```

但不應在 HARDEN-1 做大型 LLM prompt redesign。

---

### 6.7 Re-run asset preparation after extraction hardening

HARDEN-1 必須在至少一個 real-paper project 上重新跑：

```text
extraction → claim_extraction → narrative_planning
→ presentation_planning → llm_quality_rewrite（optional）
→ asset_preparation
```

檢查：

```text
- asset_plan.json 是否可建立
- paper_figure scene 是否能讀到 figures.json
- "No figure metadata found" warning 是否減少或有合理原因
- required paper_figure not found 是否有明確 warning
```

---

## 7. Output contracts

HARDEN-1 完成後，以下 artifact 應存在或可被產生：

```text
runs/{project_id}/extraction_quality_report.json
runs/{project_id}/sections.json
runs/{project_id}/figures.json
runs/{project_id}/tables.json                 # optional but recommended
runs/{project_id}/evidence_match_report.json  # per claim or aggregated
runs/{project_id}/asset_plan.json             # re-smoke output
```

`project_state.extraction` 應更新為**路徑引用**，不嵌入完整內容：

```json
{
  "text_md": "extracted_text.md",
  "sections_path": "sections.json",
  "figures_path": "figures.json",
  "tables_path": "tables.json",
  "quality_report": {
    "path": "extraction_quality_report.json",
    "quality_level": "acceptable"
  }
}
```

> **重要**：`sections`、`figures`、`tables` 的完整資料保留在各自的 artifact file 中。
> `project_state.extraction` 只存路徑與摘要欄位（如 `quality_level`）。
> 直接嵌入完整 list 會導致 project_state.json 隨論文規模膨脹，並造成 incremental update 困難。

---

## 8. Validation / quality gates

### 8.1 Extraction quality gate

Hard fail：

```text
- source.pdf unreadable
- extracted text < 500 chars
- no output files produced
- schema validation failure
```

Warning only：

```text
- missing abstract/introduction-like section
- no figures found
- figures found but no captions
- tables detected but no image extracted
- low confidence section detection
```

### 8.2 Evidence matching gate

Hard fail：

```text
- claim has empty evidence_spans
- evidence span cannot be found even after normalization/fuzzy matching
- evidence span appears to match wrong section with high risk
```

Warning only：

```text
- fuzzy match used
- short quote match used
- evidence span too short
- evidence span too long
```

### 8.3 Figure metadata gate

Hard fail：

```text
- figures.json schema invalid
- figure_id duplicates
- image_path points outside run_dir
```

Warning only：

```text
- no figure metadata found
- figure image without caption
- caption without image
- low confidence caption matching
```

---

## 9. Tests

### 9.1 Schema tests

File: `tests/test_extraction_quality_schema.py`

Must test：

```text
- ExtractedSection roundtrip
- ExtractedFigure roundtrip
- ExtractedTable roundtrip
- ExtractionQualityReport roundtrip
- EvidenceMatchReport roundtrip
- RealPaperSmokeReport roundtrip
```

---

### 9.2 Text normalization tests

File: `tests/test_text_normalization.py`

Must test：

```text
- hyphenated line breaks
- repeated whitespace
- ligatures
- line-break artifacts
- paragraph preservation where possible
```

---

### 9.3 Section detection tests

File: `tests/test_section_detection_hardening.py`

Must test：

```text
- Abstract detection
- numbered heading detection
- uppercase heading detection
- fallback Full Text section
- avoid figure caption as section
- avoid header/footer repetition as section
```

---

### 9.4 Figure extraction metadata tests

File: `tests/test_figure_extraction_metadata.py`

Must test：

```text
- figures.json is written
- figure_id deterministic
- extracted image path stays inside run_dir
- figure with caption
- figure without caption
- duplicate figure_id fails
```

---

### 9.5 Caption matching tests

File: `tests/test_caption_matching.py`

Must test：

```text
- Fig. prefix
- Figure prefix
- Table prefix
- same-page caption matching
- no caption case
- multiple captions on one page
```

---

### 9.6 Evidence matching tests

File: `tests/test_evidence_matching_hardening.py`

Must test：

```text
- exact match
- normalized exact match
- hyphenation match
- line-break match
- fuzzy match
- short quote match
- not found fail
- false positive guard: unrelated similar text should not pass
- helper works correctly when extracted_text_normalized.md is absent
- helper works correctly when extracted_text_normalized.md is present
```

---

### 9.7 Integration tests

File: `tests/test_harden1_pipeline_integration.py`

Must test：

```text
- run extraction writes extraction_quality_report.json
- extraction stage updates project_state.extraction as path references only
- project_state.extraction does NOT contain raw sections/figures lists
- claim_extraction uses hardened evidence matching helper
- asset_preparation can read figures.json when present
- old projects without figures.json still warn, not crash
- old projects without sections.json still warn, not crash
```

---

### 9.8 Real-paper smoke runner tests

File: `tests/test_harden1_real_smoke_runner.py`

Must test：

```text
- smoke runner can run a small fixture set
- RealPaperSmokeReport is written
- report contains extraction quality summary
- report records asset_plan warnings
```

---

## 10. Real-paper smoke plan

### 10.1 Smoke set

HARDEN-1 should use at least 3 papers / fixtures:

```text
Paper A: simple layout, clear sections, no complex figures
Paper B: two-column academic layout with figures and captions
Paper C: messy line breaks / hyphenation / section detection challenge
```

If real PDFs cannot be committed, use generated fixture PDFs that simulate these cases.

### 10.2 Smoke command

Preferred command:

```bash
.\.venv-win\Scripts\python.exe -m p2s_core.cli smoke real-papers --set harden1
```

Acceptable alternative:

```bash
.\.venv-win\Scripts\python.exe scripts/run_harden1_smoke.py --set harden1
```

### 10.3 Smoke output

```text
runs/{project_id}/harden1_smoke_report.json
docs/sprints/HARDEN1/reports/HARDEN1_REAL_PAPER_SMOKE.md
```

Report must summarize:

```text
- paper name / extraction quality level / section count
- figure count / caption count / claim count
- failed evidence matches / asset_plan warnings / pass/fail
```

---

## 11. Day-by-day sprint plan

### Day 1：Schema and report contracts

```text
- Add extraction / figure / quality schemas.
- Add schema exports.
- Add schema roundtrip tests.
- Create docs/sprints/HARDEN1 directory.
```

Verification:

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/test_extraction_quality_schema.py -v
```

---

### Day 2：Text normalization and section detection

```text
- Add text_normalization.py helper.
- Harden section detection.
- Write sections.json.
- Add normalization and section tests.
```

Verification:

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/test_text_normalization.py tests/test_section_detection_hardening.py -v
```

---

### Day 3：Figure and table metadata baseline

```text
- Implement / harden figure_extraction.py.
- Write figures.json.
- Add basic table caption metadata if feasible.
- Add figure / caption tests.
```

Verification:

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/test_figure_extraction_metadata.py tests/test_caption_matching.py -v
```

---

### Day 4：Extraction quality report

```text
- Generate extraction_quality_report.json.
- Update project_state.extraction as path references only (not embedded content).
- Add quality level logic.
- Ensure old projects without report still load.
```

Verification:

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/test_harden1_pipeline_integration.py -v
```

---

### Day 5：Evidence matching hardening

```text
- Extract evidence matching helper.
- Implement text source priority: normalized file if present, else raw file.
- Add EvidenceMatchReport.
- Update ClaimEvidenceReviewer to use shared helper.
- Add false positive / false negative tests.
- Add test for helper behavior when normalized file is absent.
```

Verification:

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/test_evidence_matching_hardening.py tests/test_claim_evidence_reviewer.py -v
```

---

### Day 6：Real-paper smoke set and asset_plan re-smoke

```text
- Add harden1 smoke runner.
- Run 2–3 fixture / real-paper projects.
- Re-run asset_preparation after hardened extraction.
- Write smoke report.
```

Verification:

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/test_harden1_real_smoke_runner.py -v
```

---

### Day 7：Docs, HARDEN-2 stub, full regression

```text
- Create HARDEN1_STATUS.md using standard status template.
- Create IMPLEMENTATION_PLAN_HARDEN2_SCENE_ASSET_QUALITY.md stub.
- Run full regression.
- Run manual smoke on mvp1_real_smoke or equivalent.
```

Verification:

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/ -v
```

---

## 12. Standard status template deliverable

HARDEN-1 must create `HARDEN1_STATUS.md` with the following exact structure:

```markdown
# HARDEN-1 Status

Last updated: YYYY-MM-DD

## Contract complete
- Completed artifact / schema / CLI / service contract

## Current verification
- Focused tests
- Full regression
- Manual smoke

## Known quality gaps
- Remaining data quality / real-paper / edge-case / reviewer calibration gaps

## Hardening backlog
- Items deferred to HARDEN-2 / HARDEN-3 / MVP3

## Recommended next step
- Next sprint or explicit pause point
```

This format becomes the standard for future MVP / HARDEN status documents, per Architecture Spec v8.2 Section 10A.6.

---

## 13. Acceptance criteria

HARDEN-1 is accepted only if all are true:

```text
[ ] Extraction / figure / quality schemas exist and pass roundtrip tests.
[ ] Text normalization helper exists and is test-covered.
[ ] Section detection hardening is test-covered.
[ ] sections.json is produced or a low-confidence Full Text fallback is produced.
[ ] figures.json is produced when figures exist.
[ ] Figure metadata includes figure_id / page / image_path / caption / confidence.
[ ] Missing figure captions produce warnings, not silent failure.
[ ] extraction_quality_report.json is produced.
[ ] project_state.extraction stores path references only; sections/figures content is NOT embedded in project_state.json.
[ ] Evidence matching helper is shared by reviewer/tests.
[ ] Evidence matching helper works correctly whether or not extracted_text_normalized.md exists.
[ ] EvidenceMatchReport or equivalent diagnostics are produced.
[ ] Evidence matching tests include exact, normalized, fuzzy, hyphenation, line-break, false-positive, and normalized-file-absent cases.
[ ] At least 2–3 real/synthetic real-paper smoke cases are run.
[ ] RealPaperSmokeReport or equivalent smoke summary is produced.
[ ] asset_preparation is re-run after hardened extraction on at least one project.
[ ] The previous "No figure metadata found" warning is either resolved or explicitly justified for papers without figures.
[ ] HARDEN1_STATUS.md is created using the standard template.
[ ] HARDEN-2 status is explicitly decided and recorded in HARDEN1_STATUS.md or a stub plan.
[ ] IMPLEMENTATION_PLAN_HARDEN2_SCENE_ASSET_QUALITY.md stub is created, unless HARDEN1_STATUS.md marks HARDEN-2 as superseded with justification.
[ ] No real TTS/image/video generation is introduced.
[ ] Full pytest regression passes.
```

---

## 14. Manual smoke commands

Use project-local Windows runtime:

```bash
.\.venv-win\Scripts\python.exe -m pytest tests/ -v
```

Recommended manual smoke on existing project:

```bash
.\.venv-win\Scripts\python.exe -m p2s_core.cli run --stage extraction --project mvp1_real_smoke --force
.\.venv-win\Scripts\python.exe -m p2s_core.cli run --stage claim_extraction --project mvp1_real_smoke --force
.\.venv-win\Scripts\python.exe -m p2s_core.cli run --stage narrative_planning --project mvp1_real_smoke --force
.\.venv-win\Scripts\python.exe -m p2s_core.cli run --stage presentation_planning --project mvp1_real_smoke --force
.\.venv-win\Scripts\python.exe -m p2s_core.cli run --stage llm_quality_rewrite --project mvp1_real_smoke --force
.\.venv-win\Scripts\python.exe -m p2s_core.cli run --stage asset_preparation --project mvp1_real_smoke --force
```

If real LLM calls are not available, use fake-client or fixture pipeline smoke.

Expected outputs:

```text
runs/mvp1_real_smoke/extraction_quality_report.json
runs/mvp1_real_smoke/sections.json
runs/mvp1_real_smoke/figures.json
runs/mvp1_real_smoke/claims.json
runs/mvp1_real_smoke/asset_plan.json
```

---

## 15. Post-HARDEN-1 handoff

After HARDEN-1 acceptance, proceed to:

```text
MVP2C-thin
```

Not:

```text
MVP2C-full
```

MVP2C-thin should consume:

```text
asset_plan.json
figures.json
extraction_quality_report.json
```

and produce the first minimal playable video using:

```text
Edge-TTS
text_card / static_background / selected paper figures
minimal ffmpeg composition
```

After MVP2C-thin, HARDEN-3 must be inserted before proceeding further:

```text
MVP2C-thin → HARDEN-3: Media Quality / Composition（mandatory，不可跳過）
```

HARDEN-3 will cover TTS timing, subtitle readability, segment composition, and audio loudness. It is not optional. See Architecture Spec v8.2 Section 10A.4 for the full route.

---

## 16. Final instruction to coding agent

Implement HARDEN-1 as an upstream data-quality hardening sprint.

Hard constraints:

```text
- Do not implement real media generation.
- Do not introduce ComfyUI / Playwright / ffmpeg usage.
- Do not rewrite the architecture spec.
- Do not silently overwrite old project_state fields.
- Do not embed sections/figures full content in project_state.json; use path references only.
- Do not let evidence matching helper fail or warn when extracted_text_normalized.md is absent.
- Do not silently ignore missing figure metadata.
- Do not treat MVP2B completion as quality completion.
- Produce explicit quality reports and smoke reports.
- Keep all new artifacts schema-validated and test-covered.
```

Expected major artifacts:

```text
runs/{project_id}/extraction_quality_report.json
runs/{project_id}/sections.json
runs/{project_id}/figures.json
runs/{project_id}/evidence_match_report.json
docs/sprints/HARDEN1/HARDEN1_STATUS.md
docs/sprints/HARDEN2/IMPLEMENTATION_PLAN_HARDEN2_SCENE_ASSET_QUALITY.md
```
