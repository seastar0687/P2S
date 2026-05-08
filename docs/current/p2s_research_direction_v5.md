# P2S 研究方向整理 v2

## 0. 研究定位

目前的 P2S（Paper-to-Shorts）不應只被定位為「把論文轉成短影片的工具」，而應該被提升為一個研究問題：

> AI 生成科學短影音時，如何透過 claim-grounded generation、多代理審查與人類編輯，降低錯誤、保留重點，並提升理解與傳播效果？

因此，本研究方向的核心不是單純影片合成，而是：

- AI 是否能忠實理解與壓縮學術論文？
- AI 是否能將學術內容轉譯為適合短影音的敘事？
- claim-evidence mapping 是否能降低 hallucination 與 unsupported claims？
- 多代理審查是否能提升生成內容的可信度與穩定度？
- 人類編輯者如何有效介入 AI 對論文的理解與轉譯？
- 角色化 Persona 與文案 Style 是否會影響理解度、信任感與傳播效果？
- 短影音化是否真的有助於學習、理解或傳播？

P2S 的研究定位可濃縮為：

> P2S 是一個 claim-grounded、review-guided、human-editable 的論文短影音生成系統，研究目標是探討多代理審查與人機協作介面如何提升 AI 科學知識壓縮的忠實性、可修正性與理解/傳播效果。

---

## 1. 核心系統定位

P2S 的核心系統定位應與目前工程架構保持一致：

> P2S 是一個「過程容易檢驗調整，同時具有足夠可信度、穩定度的論文短影音生成專案」。自動化是這一專案的重要方向，可調整性是輔助。

這代表 P2S 不是單純追求「輸入論文，一鍵出片」，而是追求：

```text
paper
→ claims
→ evidence mapping
→ script
→ storyboard
→ multi-agent review
→ human edit
→ video / dissemination
```

每一步都應該具備：

- 可檢查性：能看到中間結果
- 可追蹤性：每句腳本能追到 claim 與 evidence
- 可修正性：可以局部修改，不必整支重生
- 可審查性：有 reviewer agents 與 gate decision
- 可評估性：能量化忠實性、理解度與修正成本

---

## 2. 核心研究主題

目前可整理為三個主要 Research Questions，以及一個延伸研究方向。三個 RQ 形成「生成可信度 → 人類修正效率 → 理解與傳播效果」的研究鏈條；其中 **RQ1 是前置核心**，因為沒有 claim grounding 與 fidelity review，RQ2 的 inspection UI 與 RQ3 的學習/傳播評估都缺乏可信基礎。

如果研究資源只能優先完成一個方向，建議先完成 RQ1；若要形成可投稿的系統研究雛形，則以 RQ1 + RQ2 作為第一篇主線，RQ3 作為後續使用者研究或線上部署評估。

---

## RQ1：Claim-grounded multi-agent review 是否能提升腳本忠實性？

### 研究問題

> 在 AI 將論文轉換為短影音腳本的過程中，claim-grounded generation 與多代理審查機制是否能降低 hallucination、unsupported claims 與過度誇大，並提升生成內容對原論文的忠實性？

此 RQ 對應使用者提出的「大模型審查委員會」概念，也對應 P2S 系統中的 claim extraction、evidence mapping、review committee 與 revision loop。

### 核心假設

- 直接讓 LLM 從論文生成短影音腳本，容易出現重點遺漏、過度濃縮、unsupported claims 與 hype。
- 先抽取 claims 並建立 evidence mapping，可以讓後續腳本生成更可檢查。
- 多代理審查若採用結構化 rubric 與 Arbiter，而不是自由辯論，可能提升穩定性與忠實性。

### 可能的審查角色

- Contribution Reviewer：檢查是否抓到論文主要貢獻
- Evidence Reviewer：檢查腳本句子是否有原文依據
- Limitation Reviewer：檢查是否保留限制、適用範圍與失敗案例
- Hype Reviewer / Devil's Advocate：檢查是否過度誇大或短影音化後失真
- Audience Reviewer：檢查目標觀眾是否容易理解
- Script Reviewer：檢查短影音敘事是否流暢
- Arbiter：彙整各 reviewer 結果並決定 pass / revise / human_check / reject

### 研究 reviewer 與工程 reviewer 對應表

研究文件中的 reviewer 名稱是從「研究問題」切入；Architecture Spec 中的 reviewer 名稱則是從「生產流程」切入。兩者不矛盾，對應如下：

| Research reviewer | Engineering reviewer | 說明 |
|---|---|---|
| Contribution Reviewer | `PaperFidelityReviewer` + `ClaimEvidenceReviewer` | 檢查主要貢獻是否被抓到，且是否有 evidence 支持 |
| Evidence Reviewer | `ClaimEvidenceReviewer` | 檢查 claim / scene sentence 是否能對應原文 evidence |
| Limitation Reviewer | `PaperFidelityReviewer` + `DevilAdvocate` | 檢查是否保留限制、適用範圍與失敗案例 |
| Hype Reviewer | `DevilAdvocate` | 專門抓誇大、過度宣稱與錯誤類比 |
| Audience Reviewer | `ScriptQualityReviewer` + `FinalVideoReviewer` | 檢查目標觀眾能否理解、資訊密度是否合理 |
| Script Reviewer | `ScriptQualityReviewer` | 檢查短影音敘事、節奏與語句自然度 |
| Style Reviewer | `StyleConsistencyReviewer` | 檢查文案是否符合 selected style |
| Persona Reviewer | `PersonaConsistencyReviewer` | 檢查角色口吻、角色定位與聲音/表現一致性 |
| Arbiter | `Arbiter` | 彙整所有 reviewer，產生 gate decision |

### 暫定比較項目

- 暫定：單一 LLM 直接生成短影音腳本
- 暫定：LLM 生成後進行 self-review
- 暫定：claim-grounded generation，不加 multi-agent review
- 暫定：claim-grounded generation + single reviewer
- 暫定：claim-grounded generation + multi-agent review committee
- 暫定：claim-grounded generation + multi-agent review committee + human editor

### 暫定評估指標

> 以下指標仍屬初步建議；第一篇 paper 建議先鎖定 primary 指標，secondary 作為補充分析。

**Primary metrics（Research Phase A 優先）**

- unsupported claims 數量
- missing key contributions 數量
- missing limitations 數量
- overhyped / exaggerated statements 數量
- claim-evidence alignment score

**Secondary metrics**

- 暫定：hallucination 數量
- 暫定：faithfulness score
- 暫定：coverage score
- 暫定：expert rating / domain-informed rating
- 暫定：revision loops needed to pass gate

### 對應系統模組

- `paper_extraction.py`
- `claim_extraction.py`
- `script_generation.py`
- `reviewers/paper_fidelity.py`
- `reviewers/claim_evidence.py`
- `reviewers/devil_advocate.py`
- `reviewers/arbiter.py`

---

## RQ2：Human-in-the-loop inspection interface 是否能降低修正成本？

### 研究問題

> 若將 AI 生成腳本、claim、evidence mapping、risk highlighting 與 reviewer agents 的審查意見呈現在使用者介面上，是否能幫助人類更有效地修正 AI 生成的科學短影音腳本？

此 RQ 對應「用戶端介面設計」。P2S 的 UI 不應只是影片編輯器，而應是 pipeline inspection + revision console。

### 核心假設

- 一般文字編輯器不容易讓人發現 AI 腳本中的 unsupported claims。
- 若介面顯示 claim-evidence mapping，人類可以更快判斷哪些句子有風險。
- 若 reviewer comments 與 risk highlighting 能對應到特定 scene / sentence，修正成本會下降。
- 若支援 lock / regenerate / compare versions，使用者會更容易局部修正，而不是整體重做。

### 介面可能包含

- 原論文段落
- AI 抽出的 claims
- 每個 claim 對應的 evidence
- 生成的 60 秒短影音腳本
- storyboard / scene plan
- 多代理審查意見
- 高風險句子標記
- unsupported claim 標記
- limitation 缺漏提醒
- style / persona 選擇與預覽
- 人類編輯、鎖定、重生與確認流程
- revision history 與版本比較

### 暫定比較項目

- 暫定：純文字編輯介面
- 暫定：加入 reviewer comments 的編輯介面
- 暫定：加入 evidence mapping 的編輯介面
- 暫定：加入 risk highlighting 的編輯介面
- 暫定：reviewer comments + evidence mapping + risk highlighting 的整合介面
- 暫定：整合介面 + local regenerate / lock fields

### 暫定評估指標

> RQ2 第一階段建議先測修正效率與錯誤殘留，不急著同時量所有使用者心理變項。

**Primary metrics**

- editing time
- unsupported claims remaining after edit
- final script quality
- user ability to detect AI errors
- perceived workload

**Secondary metrics**

- 暫定：correction count
- 暫定：user trust
- 暫定：user confidence calibration
- 暫定：revision efficiency
- 暫定：number of unnecessary edits


### 對應系統模組

- `app/streamlit_app.py`
- `app/pages/03_claims.py`
- `app/pages/04_script.py`
- `app/pages/07_reviews.py`
- `persistence.py`
- `project_state.json`
- `revision_history`

---

## RQ3：經審查與修正的 P2S 內容是否更容易被理解或傳播？

### 研究問題

> 經過 claim-grounded generation、多代理審查與人類修正的 P2S 內容，是否比原論文摘要、一般文字摘要或未審查的 AI 腳本更有助於理解、記憶與傳播？

此 RQ 對應「實際效果評測」。可以分成 controlled study 與 online deployment 兩條路線。

### 核心假設

- 短影音腳本若未審查，可能提高吸引力但降低忠實性。
- 經過審查與修正後的短影音腳本，可能在理解、記憶與信任校準上優於一般 AI 摘要。
- 影片化與角色化不一定總是提升理解，可能增加趣味性但也可能提高認知負擔或削弱嚴謹感。

### 評測路線

1. controlled study：私下找受試者進行理解與學習成效測試
2. online deployment：將內容傳播到網路平台，觀察真實互動數據與觀眾理解情況

### 暫定比較項目

- 暫定：閱讀原論文 abstract
- 暫定：閱讀一般 LLM 文字摘要
- 暫定：閱讀未經審查的 AI-generated short script
- 暫定：閱讀經 claim-grounded generation 的 short script
- 暫定：閱讀/觀看經 multi-agent review 修正後的 short script / video
- 暫定：閱讀/觀看經 multi-agent review + human editing 修正後的 short script / video

### 暫定評估指標：controlled study

> RQ3 第一版若資源有限，建議先以 comprehension / misconception / trust calibration 作為主軸。

**Primary metrics**

- comprehension score
- main contribution identification
- limitation identification
- misconception rate
- trust calibration

**Secondary metrics**

- 暫定：retention score
- 暫定：concept recall
- 暫定：perceived clarity
- 暫定：perceived usefulness

- 暫定：cognitive load

### 暫定評估指標：online deployment

> online deployment 指標較容易受平台演算法影響，第一篇 paper 中建議作為 exploratory analysis。

**Primary / exploratory metrics**

- completion rate
- watch time
- viewer quiz response
- misunderstanding signals in comments

**Secondary metrics**

- 暫定：view count

- 暫定：like / save / share rate
- 暫定：comment quality

- 暫定：不同風格版本之間的 engagement 差異

### 對應系統模組

- `final_video.py`
- `reviewers/final_video.py`
- `export/evaluation_logs`
- `study_materials/`
- `survey/`

---

## 3. 延伸研究方向：Persona / Style 是否影響可信科學轉譯？

### 研究問題

> 在科學短影音生成中，不同 Persona 與 Style 設定是否會影響內容的忠實性、理解度、吸引力、信任感與錯誤風險？

這個方向可以作為 RQ3 的延伸，或成為第二篇 / 後續研究。它對應目前 P2S 架構中新加入的 Persona Layer 與 Style Layer。

### 為什麼這不是單純產品功能？

Persona 和 Style 不只是視覺包裝，它們會改變：

- 文案如何選擇 hook
- 是否使用比喻
- 語氣是否更口語化
- 是否更容易誇大
- 觀眾是否更願意看完
- 觀眾是否更信任內容
- 觀眾是否更容易混淆娛樂表達與科學事實

因此，它們可以被視為科學知識轉譯中的重要變因。

### 暫定比較項目

- 暫定：neutral persona + rigorous science style
- 暫定：character persona + rigorous science style
- 暫定：character persona + anime / memetic explainer style
- 暫定：neutral persona + concise academic digest style
- 暫定：same claim grounding, different style wrappers

### 暫定評估指標

- 暫定：perceived engagement
- 暫定：perceived credibility
- 暫定：trust calibration
- 暫定：comprehension score
- 暫定：misconception rate
- 暫定：style consistency score
- 暫定：persona consistency score
- 暫定：overhype risk

### 系統設計定位

在工程上：

- claim-grounded generation 是可信主線核心，不是外掛。
- style-controlled generation 是核心能力，但研究上可作為變因。
- persona-controlled generation 是產品與展示特色，研究上可作為延伸變因。

---

## 4. Claim-grounded / Style-controlled / Persona-controlled 的定位修正

前一版文件曾將 claim-grounded / style-controlled generation 視為「第 4 類貢獻：外掛模組」。根據目前 P2S 架構的發展，這裡需要修正。

### 4.1 Claim-grounded generation：主線核心

Claim-grounded generation 不應只是外掛，因為 P2S 的可信度根本依賴它。

它負責：

- 從論文抽取 claims
- 將 claims 對應到原文 evidence
- 產生可追蹤的短影音腳本
- 讓 reviewer 能判斷每句話是否被支持
- 讓人類使用者能快速檢查高風險句子

因此它應該是 P2S pipeline 的核心階段。

### 4.2 Style-controlled generation：核心能力 / 可研究變因

Style-controlled generation 應是 P2S 的核心能力，因為短影音轉譯必然涉及風格控制。

但在研究設計上，它可以被視為支援 RQ1 / RQ2 / RQ3 的模組，也可以在延伸研究中作為實驗變因。

可能支援的風格包括：

- Academic style
- Popular science style
- Shorts hook style
- Anime character explanation style
- Conference preview style
- Critical review style
- Calm paper digest style

### 4.3 Persona-controlled generation：產品特色 / 延伸研究變因

Persona-controlled generation 包含角色姓名、個性、定位、VRM 3D 模型、TTS 語音模型、語音訓練資料、表情動作與角色說話規則。

在第一階段研究中，Persona 不一定要作為主要變因；但系統架構應保留 Persona Layer，因為它對 P2S 的長期展示、短影音系列化與角色化科普非常重要。

---

## 5. 目前建議的最小可行研究版本：Research Phase A

為避免和工程文件中的 **Engineering MVP 0** 混淆，研究文件不再使用「MVP0」作為階段名稱。

- **Engineering MVP 0**：兩週 sprint contract，只做 schema、CLI、state、persona/style loader 與 PDF 純文字 extraction。
- **Research Phase A**：第一個可研究閉環，目標是能評估 RQ1 / RQ2 的可信文字轉譯流程。

換句話說，Research Phase A 比 Engineering MVP 0 大，約等於 Engineering MVP 0 + 0.5 + 1 + 3 的簡化組合。

第一階段不必急著完成完整影片合成。研究價值較高的部分可以先集中在影片生成之前：

1. PDF / paper parsing
2. claim extraction
3. evidence mapping
4. 60 秒短影音腳本生成
5. storyboard / scene plan 生成
6. multi-agent review
7. human-in-the-loop editing interface
8. 修正前後品質評估

第一版研究可以先做到：

> paper → claims → evidence → script → storyboard → review → human edit → evaluation

影片合成可以作為後續 demo 或系統完整化階段，而不是第一階段 paper 的核心。

### Research Phase A：可信文字研究閉環

```text
Research Phase A
PDF → extracted_text.md → claims.json → scenes.json → script_review.json → Streamlit inspection UI
```

Research Phase A 必須包含：

- `PaperClaim` schema
- `EvidenceSpan` schema
- `SceneDraft` / `Scene` schema
- `ReviewResult` schema
- `project_state.json`
- claim-evidence mapping
- script generation
- at least 3 reviewers：Paper Fidelity / Claim Evidence / Hype or Devil's Advocate
- basic Arbiter
- simple Streamlit UI：檢視 claims、script、review findings，支援人工修改

Research Phase A 暫不包含：

- 完整影片合成
- VRM 角色渲染
- TTS voice training
- 複雜 ComfyUI workflow
- 線上平台部署

### Research Phase A 對應 RQ

- 對 RQ1：可測試 claim-grounded + multi-agent review 是否提升忠實性。
- 對 RQ2：可測試 inspection UI 是否降低人工修正成本。
- 對 RQ3：可先用 script / storyboard 版本做小型理解測試，影片化留到 Research Phase C。

---

## 6. Research Phase 與 Engineering MVP 對應

兩份文件使用不同階段命名：研究文件關心「能回答什麼研究問題」，工程文件關心「接下來能交付什麼功能」。為避免混淆，對應如下。

| Research phase | 研究目的 | 對應 Engineering MVP | 工程內容摘要 |
|---|---|---|---|
| Research Phase A：可信文字研究閉環 | 回答 RQ1，初步支援 RQ2 | MVP 0 + MVP 0.5 + MVP 1 + MVP 3（簡化版） | schema/state/CLI、persona/style loader、PDF→claims→script、基本 reviewer gate |
| Research Phase B：人機協作審查介面 | 回答 RQ2 | MVP 4 | Streamlit inspection UI、claim table、scene editor、review dashboard、lock/regenerate |
| Research Phase C：影片化與理解/傳播評估 | 回答 RQ3 | MVP 2 + MVP 5 | TTS、visual planning、segments、final video、controlled study / online deployment |
| Research Phase D：Persona / Style 變因研究 | 延伸 RQ3 或後續研究 | MVP 3 + MVP 6+ | Persona/Style 強化、persona acquisition、角色化與風格變因比較 |

### 後續 Research Phase 說明

#### Research Phase B：Human-in-the-loop inspection UI

```text
claims + evidence + script + reviewer findings → inspection UI → human edit logs
```

目標：檢驗 reviewer comments、evidence mapping、risk highlighting、local regenerate / lock fields 是否降低人工修正成本。

#### Research Phase C：影片化與傳播評估

```text
reviewed script → TTS → visual planning → final video → final review → evaluation
```

目標：檢驗經審查與修正的 P2S 內容是否提升理解、記憶、信任校準與傳播效果。

#### Research Phase D：Persona / Style 變因研究

```text
same claim grounding → different persona/style wrappers → compare engagement / credibility / misconception risk
```

目標：研究角色化與風格控制是否提升吸引力，或是否引入過度娛樂化與誤解風險。

## 7. 可能的研究標題

暫定標題方向：

- Review-Guided Paper-to-Shorts: Human-AI Collaborative Generation of Faithful Scientific Short Videos
- From Papers to Shorts: A Multi-Agent Review Framework for Faithful Scientific Video Generation
- Human-in-the-Loop Scientific Short Video Generation with Multi-Agent Review and Claim Grounding
- Faithful Academic Knowledge Compression for Short-Form Scientific Video Generation
- Claim-Grounded Paper-to-Shorts: Multi-Agent Review and Human Editing for Scientific Video Scripts
- Inspectable Paper-to-Shorts: Claim-Grounded Scientific Video Script Generation with Human-AI Review
- Persona- and Style-Controlled Scientific Shorts: Balancing Engagement and Faithfulness in AI-Generated Research Communication

---

## 8. 可能的投稿方向

### 偏多模態生成 / 媒體系統

- ACM Multimedia
- ICME
- ACM Multimedia Workshop / Demo Track

### 偏人機協作 / 介面設計

- CHI
- DIS
- UIST
- CHI Workshop / Late-Breaking Work

### 偏學習效果 / 教育科技

- LAK
- AIED
- ICER

### 偏科學傳播 / 線上平台

- CSCW
- ICWSM

### 偏 AI evaluation / trustworthy generation

- ACL / EMNLP Workshop
- NeurIPS Workshop
- ICLR Workshop
- FAccT Workshop

---

## 9. 目前方向總結

目前 P2S 研究方向可濃縮為：

> 研究 AI 生成科學短影音時，如何透過 claim-grounded generation、多代理審查、人類編輯介面與效果評測，使學術知識能被忠實、可控且有效地壓縮為短影音內容。

其中：

- RQ1 是 claim-grounded generation + multi-agent review / 大模型審查委員會
- RQ2 是 human-in-the-loop interface / 用戶端審查與編輯介面
- RQ3 是 learning / understanding / dissemination evaluation
- Persona / Style 是可控生成與傳播效果的重要延伸變因
- 影片合成是完整系統的重要 demo，但第一階段研究核心可以先放在 script / storyboard / review / human editing

此方向的關鍵，是避免讓 P2S 停留在 side project，而是將其提升為：

> AI scientific knowledge compression, review, and human-AI collaborative editing 的研究問題。

---

## 10. 下一步建議

目前已經有三份文件分工：

```text
docs/current/p2s_research_direction_v5.md                 → 研究問題、RQ、評估設計、投稿方向
docs/current/P2S_redesign_architecture_v8.1.md             → 長期完整工程架構與系統藍圖
docs/sprints/MVP0/IMPLEMENTATION_PLAN_MVP0_v3.md           → 兩週 sprint contract，實際開工依據
```

下一步不應再擴張研究方向，而是先照 `docs/sprints/MVP0/IMPLEMENTATION_PLAN_MVP0_v3.md` 完成 Engineering MVP 0 + 0.5：

1. 建立 schema / project_state / stage status。
2. 建立 CLI：`p2s init` / `p2s run --stage extraction` / `p2s status`。
3. 建立 persona/style loader 與 `seina`、`rigorous_science_short` 範例。
4. 完成 PyMuPDF 純文字 extraction。
5. 讓 smoke tests 全部通過。

Engineering MVP 0 + 0.5 完成後，才進入 Engineering MVP 1，開始實作 claim extraction、evidence mapping 與 script generation。當 Engineering MVP 1 + MVP 3 的簡化版完成後，才等於本文件所稱的 **Research Phase A：可信文字研究閉環**。
