# P2S Implementation Plan — MVP 0 + MVP 0.5

> **這份文件是 sprint contract，不是設計文件。**
> 完整架構設計請見 `P2S_redesign_architecture_v7.md`（以下簡稱 "Architecture Spec"）。
> 本文只描述**接下來 1-2 週要交付什麼**、**驗收標準是什麼**、**什麼不能做**。

---

## 0. Sprint 目標（一句話版本）

**讓「`p2s init paper.pdf` → `p2s run --stage extraction` → `p2s status`」這條最小指令鏈跑得通，且所有資料結構與 persona/style 載入機制已就位。**

不生影片。不接 LLM 真實邏輯。不做 UI。只做骨架與 schema。

---

## 1. 範圍邊界（Scope Discipline）

### ✅ MVP 0 / 0.5 必做

```
1. 所有 Pydantic schema 建立並可序列化/反序列化
2. ConfigManager 能讀 config.yaml + 解析 ${ENV_VAR}
3. LLMService 最小版（OpenAI provider only，能跑通一次 hello world 即可）
4. persistence.py（load/save/snapshot project_state.json）
5. CLI：p2s init / p2s run / p2s status
6. Persona / Style 載入器（只載入降級版欄位）
7. Persona / Style compatibility check（deterministic rule，非 LLM）
8. personas/seina/ + styles/rigorous_science_short/ 各一個範例
9. extraction stage 能跑（用 PyMuPDF 抽純文字即可，不抽圖、不分 section）
10. smoke test 四組：schema serialization / pipeline init→run→status / persona-style load / compatibility check
```

### ⛔ 本 sprint 嚴禁碰

```
✗ Reviewer committee（任何 LLM judge 邏輯）
✗ Claim extraction（用 LLM 從文字抽出 PaperClaim）
✗ Script generation（任何文字到腳本的 LLM 流程）
✗ TTS / image / video 生成（任何媒體服務）
✗ Streamlit UI（任何 web 介面）
✗ VRM rendering / voice cloning / 角色動作
✗ figure_extraction.py 的真實實作（先空著或拋 NotImplementedError）
✗ 多 style / 多 persona（只做 seina + rigorous_science_short）
✗ Hot reload（ConfigManager 第一版同步讀取即可）
✗ 不同 LLM provider 切換（OpenAI 寫死即可）
```

**判斷準則：如果某個功能在 MVP 0.5 完成前不會被「`p2s init / run / status`」三指令觸發，就不該寫。**

---

## 2. Deliverables 清單

### 2.1 檔案結構（精確版）

```
p2s/
├── config.yaml                          ← 從 Architecture Spec 1.1 複製最小欄位
├── requirements.txt                     ← 從 Architecture Spec 9.4 複製
├── README.md                            ← 三段話：專案是什麼、怎麼裝、怎麼跑 hello world
├── .env.example                         ← OPENAI_API_KEY=sk-xxx
├── p2s_core/
│   ├── __init__.py
│   ├── config.py                        ← ConfigManager
│   ├── core.py                          ← P2SCore（只組裝 service，不跑 pipeline）
│   ├── cli.py                           ← Click CLI 入口
│   ├── models/
│   │   ├── __init__.py
│   │   ├── common.py                    ← EvidenceSpan, SuggestedFix
│   │   ├── claim.py                     ← PaperClaim
│   │   ├── scene.py                     ← Scene, SceneDraft, VoiceDirection
│   │   ├── review.py                    ← ReviewResult, GateDecision
│   │   ├── persona.py                   ← PersonaProfile, VRMProfile, VoiceProfile, VisualIdentityProfile
│   │   ├── style.py                     ← StyleProfile
│   │   └── project_state.py             ← ProjectState（含 stages, revision_history）
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm_service.py               ← LLMService（OpenAI only, 含 retry）
│   │   ├── persistence.py               ← load/save/snapshot
│   │   ├── paper_extraction.py          ← 用 PyMuPDF 抽純文字到 extracted_text.md（不分 section）
│   │   └── persona_style.py             ← Persona/Style loader + compatibility check
│   ├── pipelines/
│   │   ├── __init__.py
│   │   ├── base.py                      ← BasePipeline（template method）
│   │   └── paper_summary.py             ← PaperSummaryPipeline（只實作 setup + extraction stage）
│   ├── personas/
│   │   └── seina/
│   │       ├── persona.yaml             ← MVP 降級欄位（見 Architecture Spec 3A.7）
│   │       ├── prompt_profile.md
│   │       ├── speaking_rules.md
│   │       └── examples/
│   │           └── short_explainer_01.md
│   └── styles/
│       └── rigorous_science_short/
│           ├── style.yaml               ← MVP 降級欄位（見 Architecture Spec 3B.6）
│           ├── prompt_guide.md
│           ├── forbidden_phrases.txt
│           └── examples/
│               ├── good_01.md
│               └── bad_overhyped.md
└── tests/
    ├── __init__.py
    ├── test_schema.py                   ← 所有 schema 可 model_dump → json → model_validate
    ├── test_persona_style_load.py       ← 載入 seina + rigorous_science_short 不報錯
    ├── test_compatibility_check.py      ← Persona/Style compatibility deterministic rule
    └── test_pipeline_smoke.py           ← init → run extraction → status 全程不 crash
```

### 2.2 Schema 完整清單

直接照 Architecture Spec 5.0 / 5.1 / 5.3 / 5.4 / 3A.3-3A.5 / 3B.2 抄。

**注意 schema 一致性的兩個雷區**：

```
1. visual_type 在 SceneDraft 與 Scene 都要是：
   Literal["paper_figure", "diagram", "metaphor_image", "character", "static_template"]
   （不是 "static"）

2. PersonaProfile.vrm 與 PersonaProfile.visual_identity 在 MVP 0.5 永遠 = None
   （schema 保留，但實作不接）
```


### 2.3A ProjectState 最小 schema（本 sprint 必須明確）

雖然完整 schema 仍以 Architecture Spec 為準，但本 sprint 實作時至少要有以下頂層欄位，避免開發者在長文件中搜尋：

```python
class ProjectSource(BaseModel):
    pdf_path: str
    title: str | None = None
    authors: list[str] = []
    doi: str | None = None
    arxiv_id: str | None = None

class ProjectSettings(BaseModel):
    target_duration_sec: int = 60
    language: str = "zh-TW"
    target_audience: str = "general_science"
    use_character: bool = False
    use_paper_figures: bool = True
    video_orientation: Literal["vertical", "horizontal"] = "vertical"

class ExtractionState(BaseModel):
    text_md: str | None = None
    sections: list[dict] = []
    figures: list[dict] = []
    tables: list[dict] = []
    quality_report: dict = {}

class StageState(BaseModel):
    status: Literal["pending", "running", "done", "failed", "needs_review", "rejected"] = "pending"
    started_at: str | None = None
    finished_at: str | None = None
    output_paths: list[str] = []
    error: str | None = None
    revision_count: int = 0

class ProjectState(BaseModel):
    project_id: str
    created_at: str
    source: ProjectSource
    settings: ProjectSettings
    persona: dict
    style: dict
    extraction: ExtractionState = ExtractionState()
    claims: list[PaperClaim] = []
    script: dict = {"target_duration": 60, "audience": "general_science", "scenes": []}
    storyboard: dict = {"frames": []}
    assets: dict = {"images": [], "audio": [], "segments": []}
    reviews: list[ReviewResult] = []
    revision_history: list[dict] = []
    final_video: dict = {"path": None, "status": "draft"}
    stages: dict[str, StageState]
```

MVP 0.5 的 `stages` 至少要初始化以下 key：

```text
extraction, claim_extraction, narrative_planning, script_generation,
storyboard_planning, asset_generation, composition, final_review
```

### 2.3B CLI 介面（明確規格）

```bash
# 初始化新專案
p2s init <pdf_path> [--persona seina] [--style rigorous_science_short] [--id <project_id>]

# 行為：
# 1. 在 runs/ 下建立 {project_id}/ 目錄
# 2. 複製 PDF 到 runs/{project_id}/source.pdf
# 3. 載入指定的 persona / style
# 4. 寫入 project_state.json，所有 stages 設為 pending
# 5. 印出 project_id 與目錄路徑
```

```bash
# 執行某個 stage
p2s run --stage <stage_name> [--project <project_id>] [--force]

# 行為：
# 1. 讀取 project_state.json
# 2. 檢查前置 stage 是否 done（不然拒絕執行）
# 3. 將該 stage status 設為 running
# 4. 執行對應 service
# 5. 成功則設為 done，失敗則設為 failed 並記錄 error
# 6. snapshot 修改前的 project_state.json（時間戳）
# 7. --force 可強制重跑已 done 的 stage

# MVP 0.5 只需支援 stage = extraction
# 其他 stage 應拋 NotImplementedError 並提示「此 stage 將在 MVP 1+ 實作」
```

```bash
# 查看狀態
p2s status [--project <project_id>]

# 行為：
# 印出所有 stage 的當前 status，例如：
#
# Project: 2026-05-05_abc123
# Persona: seina (v0.1.0)
# Style:   rigorous_science_short (v0.1.0)
#
# Stages:
#   ✓ extraction          done       (45s, 2026-05-05 10:01:23)
#   ○ claim_extraction    pending
#   ○ narrative_planning  pending
#   ...
```

```bash
# 驗證所有 Persona package
python -m p2s_core.cli validate-personas

# 行為：
# 1. 掃描 config.paths.personas_dir 下所有 */persona.yaml
# 2. 用 PersonaProfile.model_validate() 驗證 schema
# 3. 檢查 prompt_profile.md / speaking_rules.md / examples/ 是否存在
# 4. 每個 persona 印出 valid / invalid 與錯誤原因
# 5. 全部 valid → exit code 0；任一 invalid → exit code 1
#
# 範例輸出：
# ✓ personas/seina/persona.yaml: valid
```

```bash
# 驗證所有 Style package
python -m p2s_core.cli validate-styles

# 行為：
# 1. 掃描 config.paths.styles_dir 下所有 */style.yaml
# 2. 用 StyleProfile.model_validate() 驗證 schema
# 3. 檢查 prompt_guide.md / forbidden_phrases.txt / examples/ 是否存在
# 4. 每個 style 印出 valid / invalid 與錯誤原因
# 5. 全部 valid → exit code 0；任一 invalid → exit code 1
#
# 範例輸出：
# ✓ styles/rigorous_science_short/style.yaml: valid
```


### 2.3C persistence.py 與 snapshot 規格

`persistence.py` 必須提供以下同步函式即可，不需要資料庫：

```python
def load_state(project_id: str) -> ProjectState: ...
def save_state(state: ProjectState) -> None: ...
def snapshot(project_id: str, filename: str = "project_state.json") -> str: ...
def list_revisions(project_id: str) -> list[str]: ...
```

Snapshot 觸發規則：

```text
1. `p2s init` 第一次建立 project_state.json 時，不建立 snapshot。
2. `p2s run --stage extraction` 在修改 state 前，先 snapshot 當前 project_state.json。
3. 若 stage 從 pending → running → done/failed，至少保存一次修改前 snapshot。
4. `--force` 重跑已 done stage 時，一定先 snapshot：
   project_state_YYYYMMDDTHHMMSS.json
5. `save_state()` 本身只負責覆寫當前 project_state.json；是否 snapshot 由 caller 決定。
```

原則：**snapshot 是 stage runner 的責任，不是 save_state 的隱式副作用**。這樣行為比較可預測，測試也比較容易寫。

### 2.4 LLMService 範圍

**MVP 0.5 不需要真的呼叫 LLM**。LLMService 只需：

```python
class LLMService:
    def __init__(self, config: dict):
        self.provider = config["llm"]["provider"]  # 只認 "openai"
        self.model = config["llm"]["model"]
        self.api_key = config["llm"]["api_key"]
        self.client = httpx.AsyncClient(timeout=30)

    async def complete(self, messages, response_type=None, ...) -> str | BaseModel:
        # MVP 0.5 階段，這個 method 寫好但只在 smoke test 中呼叫一次
        # （測試「你好」→ 回傳任何字串即可）
        ...

    async def health_check(self) -> bool:
        """smoke test 用，呼叫一次 LLM 確認 API key 有效。"""
        ...
```

不需要：batch、structured output fallback、provider 切換、task overrides。這些是 MVP 1+。

### 2.5 paper_extraction.py 範圍

**MVP 0.5 階段，只做最簡單的純文字抽取**：

```python
def extract_text(pdf_path: str) -> str:
    """用 PyMuPDF 抽純文字，不分 section、不抽圖、不抽表。"""
    import fitz  # PyMuPDF
    doc = fitz.open(pdf_path)
    text = "\n\n".join(page.get_text() for page in doc)
    return text

def run_extraction_stage(state: ProjectState) -> ProjectState:
    text = extract_text(state.source.pdf_path)
    output_path = f"runs/{state.project_id}/extracted_text.md"
    Path(output_path).write_text(text, encoding="utf-8")
    state.extraction.text_md = output_path
    state.stages["extraction"].status = "done"
    return state
```

不做：
- section detection
- figure extraction
- OCR fallback
- quality gate check

這些是 MVP 1。


### 2.6 Persona / Style compatibility check 範圍

MVP 0.5 只做 deterministic rule，不做 LLM reviewer。

```python
def check_persona_style_compatibility(persona: PersonaProfile, style: StyleProfile) -> list[str]:
    """Return warning messages. Empty list means compatible enough for MVP 0.5."""
    warnings = []

    # 例：嚴謹度很高，但 persona 描述中有過度戲劇化傾向 → warning
    dramatic_keywords = ["dramatic", "overexcited", "clickbait", "誇張", "戲劇化"]
    if style.rigor_level >= 4:
        text = " ".join(persona.personality_traits + [persona.speaking_style_summary])
        if any(k in text for k in dramatic_keywords):
            warnings.append("high-rigor style may conflict with dramatic persona tone")

    return warnings
```

驗收：`test_compatibility_check.py` 至少包含：

```text
✓ seina + rigorous_science_short → warnings 為空或只有 low-risk warning
✓ artificial_dramatic_persona + rigorous_science_short → 產生 warning
```

---

## 3. 驗收標準（Definition of Done）

### 3.1 自動化測試必須全綠

```bash
pytest tests/ -v
```

三個 smoke test 全過：

```
tests/test_schema.py
  ✓ test_evidence_span_roundtrip
  ✓ test_paper_claim_roundtrip
  ✓ test_scene_roundtrip
  ✓ test_persona_profile_roundtrip
  ✓ test_style_profile_roundtrip
  ✓ test_project_state_roundtrip
  ✓ test_scene_visual_type_consistency  # ← Scene 與 SceneDraft 的 Literal 必須一致

tests/test_persona_style_load.py
  ✓ test_load_seina_persona
  ✓ test_load_rigorous_science_short_style
  ✓ test_persona_vrm_is_none_in_mvp     # ← 確保降級

tests/test_compatibility_check.py
  ✓ test_seina_rigorous_style_compatible
  ✓ test_dramatic_persona_warns_with_high_rigor_style

tests/test_pipeline_smoke.py
  ✓ test_init_creates_project_state
  ✓ test_run_extraction_stage
  ✓ test_status_command_after_init
  ✓ test_run_unimplemented_stage_raises_not_implemented
```

### 3.2 手動端到端測試

把這份論文 PDF（任挑一篇 arXiv 上的 ML paper）放進去：

```bash
$ p2s init paper.pdf
Created project: 2026-05-05_a1b2c3
  → runs/2026-05-05_a1b2c3/
  → persona: seina
  → style: rigorous_science_short

$ p2s run --stage extraction
Running stage: extraction
  ✓ Extracted 12,453 chars from paper.pdf
  → runs/2026-05-05_a1b2c3/extracted_text.md
  ✓ Stage extraction: done (1.2s)

$ p2s status
Project: 2026-05-05_a1b2c3
Stages:
  ✓ extraction          done       (1.2s)
  ○ claim_extraction    pending
  ○ ...
```

驗收要求：

```
✓ runs/2026-05-05_a1b2c3/source.pdf 存在
✓ runs/2026-05-05_a1b2c3/project_state.json 存在且 schema 合法
✓ runs/2026-05-05_a1b2c3/extracted_text.md 存在且非空
✓ project_state.json 中 stages.extraction.status == "done"
✓ project_state.json 中 persona.persona_id == "seina"
✓ 中斷後再 p2s status 仍顯示正確進度
```

### 3.3 Schema Linting

```bash
# Pydantic 驗證所有 yaml 範例
python -m p2s_core.cli validate-personas
python -m p2s_core.cli validate-styles

# 必須全部通過：
# ✓ personas/seina/persona.yaml: valid
# ✓ styles/rigorous_science_short/style.yaml: valid
```

### 3.4 文件完整性

```
✓ README.md 包含：安裝指令、第一個 hello world 範例、CLI 三指令說明
✓ .env.example 包含 OPENAI_API_KEY 範例
✓ requirements.txt 與 Architecture Spec 9.4 一致
✓ config.yaml 至少包含：llm / paths / extraction 三個區塊
```

---

## 4. 時程估計（兩週 sprint）

| 天數 | 任務 |
|---|---|
| Day 1 | 環境建置、requirements、config.yaml、目錄骨架 |
| Day 2-3 | 所有 Pydantic schema（models/）+ test_schema.py |
| Day 4 | persistence.py + project_state load/save/snapshot |
| Day 5 | LLMService 最小版 + health_check + 連線測試 |
| Day 6 | persona/style yaml loader + compatibility check + tests |
| Day 7 | personas/seina/ 與 styles/rigorous_science_short/ 範例填寫 |
| Day 8 | paper_extraction.py（PyMuPDF 純文字版） |
| Day 9 | BasePipeline + PaperSummaryPipeline 骨架 |
| Day 10 | CLI（init / run / status）+ Click 整合 |
| Day 11 | test_pipeline_smoke.py + 端到端手動測試 |
| Day 12 | 文件（README / .env.example）+ bug 修復 |
| Day 13-14 | Buffer / 修復 / 同 sprint review |

**警示信號**：

- 如果在 Day 5 還在跟 LLMService 結構化輸出搏鬥 → 砍掉，只留 health_check
- 如果在 Day 8 還在做 PDF section detection → 砍掉，只抽純文字
- 如果在 Day 10 想順便做 Streamlit UI → 不要，等 MVP 4

---

## 5. 完成後的下一步（不在本 sprint）

下個 sprint（MVP 1）的範圍：

```
1. claim_extraction.py：真實接 LLM，從 extracted_text.md 抽 PaperClaim
2. paper_extraction.py 升級：section detection、figure extraction
3. script_generation.py：真實接 LLM，從 claims 生 SceneDraft
4. 第一個 reviewer：PaperFidelityReviewer（純規則檢查 + 簡單 LLM judge）
5. tests/golden/ 開始建立 5 篇論文的 expected_claims
```

但這些**都不是本 sprint 的範圍**。本 sprint 結束時，能跑通骨架、能載入 persona/style、能抽 PDF 純文字、所有 schema 就位，就達成目標。

---

## 6. 給實作者的提醒

1. **先寫測試，再寫實作**。所有 schema 都應該先寫 roundtrip test 再寫 schema 本身。
2. **不要追求一次寫對**。先讓 test 通過 happy path，邊界情況留到 MVP 1+。
3. **遇到誘惑要 Say No**。「順便做一下 ComfyUI 接口」「順便接 Streamlit」都是失焦陷阱。
4. **每天結束前 commit**，即使是半成品。便於回退。
5. **遇到 Architecture Spec 與本 plan 衝突時，以本 plan 為準**。Architecture Spec 是長期目標，本 plan 是當前現實。

---

## 7. 與 Architecture Spec 的對應索引

| 本文章節 | 對應 Architecture Spec 章節 |
|---|---|
| Schema 規格 | 5.0、5.1、5.3、5.4、3A.3-3A.5、3B.2 |
| config.yaml 範例 | 1.1 |
| LLMService 介面 | 1.2 |
| Stage 狀態機 | 6.0 |
| Phase 1 範圍（extraction） | 6 / Phase 1 |
| Persona MVP 降級 | 3A.7 |
| Style MVP 降級 | 3B.6 |
| requirements.txt | 9.4 |
| 目錄結構（完整版） | 4 |

完整設計細節在 Architecture Spec，本文不重複。
