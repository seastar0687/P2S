from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

from p2s_core.config import load_config
from p2s_core.models import ClaimExtractionResult, ClaimReviewBundle, PaperClaim, ProjectState
from p2s_core.reviewers import Arbiter, ClaimEvidenceReviewer, PaperFidelityReviewer
import p2s_core.services.persistence as persistence
from p2s_core.services.llm_service import LLMService
from p2s_core.services.text_chunking import build_extracted_paper, estimate_tokens


SECTION_PRIORITY = {
    "abstract": 0,
    "introduction": 1,
    "method": 2,
    "experiment": 3,
    "result": 4,
    "discussion": 5,
    "limitation": 6,
    "conclusion": 7,
    "background": 8,
    "unknown": 9,
}


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def load_prompt(path: str | Path = "p2s_core/prompts/claim_extraction_v1.md") -> str:
    return Path(path).read_text(encoding="utf-8")


async def extract_claims(
    project_id: str,
    extracted_text: str,
    llm: LLMService,
    max_tokens_per_chunk: int = 800,
    max_source_tokens: int = 6000,
    prompt_path: str | Path = "p2s_core/prompts/claim_extraction_v1.md",
    debug_dir: str | Path | None = None,
) -> ClaimExtractionResult:
    paper = build_extracted_paper(
        project_id=project_id,
        text=extracted_text,
        max_tokens_per_chunk=max_tokens_per_chunk,
    )
    selected_chunks = select_chunks_for_claim_extraction(
        paper.chunks,
        max_source_tokens=max_source_tokens,
    )
    prompt = load_prompt(prompt_path)
    chunk_payload = [
        {
            "chunk_id": chunk.chunk_id,
            "section_id": chunk.section_id,
            "section_type": chunk.section_type,
            "text": chunk.text,
        }
        for chunk in selected_chunks
    ]

    result = await llm.complete(
        [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"project_id={project_id}\nchunks={chunk_payload}"},
        ],
        response_type=ClaimExtractionResult,
        temperature=0.2,
        debug_dir=debug_dir,
    )
    if not isinstance(result, ClaimExtractionResult):
        raise TypeError("LLMService returned unexpected non-ClaimExtractionResult")

    return _normalize_result(result, project_id, selected_chunks, llm.model)


def select_chunks_for_claim_extraction(chunks, max_source_tokens: int = 6000):
    selected = []
    used_tokens = 0
    for chunk in sorted(chunks, key=lambda item: (SECTION_PRIORITY.get(item.section_type, 99), item.chunk_id)):
        tokens = chunk.token_estimate or estimate_tokens(chunk.text)
        if selected and used_tokens + tokens > max_source_tokens:
            continue
        selected.append(chunk)
        used_tokens += tokens
        if used_tokens >= max_source_tokens:
            break
    return selected or chunks[:1]


def _normalize_result(result, project_id: str, chunks, model_name: str) -> ClaimExtractionResult:
    valid_chunk_ids = {chunk.chunk_id for chunk in chunks}
    accepted: list[PaperClaim] = []
    invalid_candidates = list(result.quality_report.get("invalid_candidates", []))

    for claim in result.claims:
        if not claim.evidence_spans:
            invalid_candidates.append(
                {
                    "claim_text": claim.claim_text,
                    "reason": "missing_evidence",
                    "source_chunk_id": claim.source_section,
                }
            )
            continue
        accepted.append(claim)

    quality_report = dict(result.quality_report)
    quality_report["invalid_candidates"] = invalid_candidates
    quality_report["claim_count"] = len(accepted)

    return ClaimExtractionResult(
        project_id=project_id,
        claims=accepted,
        source_chunk_ids=[
            chunk_id for chunk_id in result.source_chunk_ids if chunk_id in valid_chunk_ids
        ] or [chunk.chunk_id for chunk in chunks],
        extraction_model=result.extraction_model or model_name,
        prompt_version=result.prompt_version,
        created_at=result.created_at or utc_now(),
        quality_report=quality_report,
    )


def run_claim_extraction_stage(
    state: ProjectState,
    llm: LLMService | None = None,
    config_path: str | Path = "config.yaml",
) -> ProjectState:
    project_dir = persistence.project_dir(state.project_id)
    extracted_path = Path(state.extraction.text_md or project_dir / "extracted_text.md")
    if not extracted_path.exists():
        raise FileNotFoundError(f"extracted_text.md not found: {extracted_path}")

    extracted_text = extracted_path.read_text(encoding="utf-8")
    if not extracted_text.strip():
        raise ValueError("extracted_text.md is empty")

    own_llm = llm is None
    if llm is None:
        config = load_config(config_path)
        if not config.get("llm", {}).get("api_key"):
            raise ValueError("OPENAI_API_KEY is not set. Please configure it before real LLM stages.")
        llm = LLMService(config)

    debug_dir = project_dir / "debug"
    if own_llm:
        result = asyncio.run(
            _extract_claims_and_close(
                project_id=state.project_id,
                extracted_text=extracted_text,
                llm=llm,
                debug_dir=debug_dir,
            )
        )
    else:
        result = asyncio.run(
            extract_claims(
                project_id=state.project_id,
                extracted_text=extracted_text,
                llm=llm,
                debug_dir=debug_dir,
            )
        )

    claims_path = project_dir / "claims.json"
    claims_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

    review_bundle = review_claim_extraction_result(result, extracted_text)
    reviews_dir = project_dir / "reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)
    review_path = reviews_dir / "claim_review_rev001.json"
    review_path.write_text(review_bundle.model_dump_json(indent=2), encoding="utf-8")

    state.claims = result.claims
    state.reviews.extend(review_bundle.reviews)
    if review_bundle.gate_decision.status == "pass":
        state.stages["claim_extraction"].status = "done"
    elif review_bundle.gate_decision.status == "human_check":
        state.stages["claim_extraction"].status = "needs_review"
    else:
        state.stages["claim_extraction"].status = "rejected"
    state.stages["claim_extraction"].output_paths = [str(claims_path), str(review_path)]
    return state


def review_claim_extraction_result(
    result: ClaimExtractionResult,
    extracted_text: str,
) -> ClaimReviewBundle:
    reviews = []
    evidence_reviewer = ClaimEvidenceReviewer()
    fidelity_reviewer = PaperFidelityReviewer()
    for claim in result.claims:
        reviews.append(evidence_reviewer.review(claim, extracted_text))
        reviews.append(fidelity_reviewer.review(claim))

    gate_decision = Arbiter().decide(reviews, total_claims=len(result.claims))
    return ClaimReviewBundle(
        project_id=result.project_id,
        reviews=reviews,
        gate_decision=gate_decision,
        created_at=utc_now(),
    )


async def _extract_claims_and_close(project_id: str, extracted_text: str, llm: LLMService, debug_dir):
    try:
        return await extract_claims(
            project_id=project_id,
            extracted_text=extracted_text,
            llm=llm,
            debug_dir=debug_dir,
        )
    finally:
        await llm.aclose()
