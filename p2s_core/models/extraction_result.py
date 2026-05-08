from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from p2s_core.models.claim import PaperClaim
from p2s_core.models.review import GateDecision, ReviewResult


class ClaimExtractionResult(BaseModel):
    project_id: str
    claims: list[PaperClaim]
    source_chunk_ids: list[str]
    extraction_model: str | None = None
    prompt_version: str = "claim_extraction_v1"
    created_at: str
    quality_report: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def accepted_claims_must_have_evidence(self) -> "ClaimExtractionResult":
        missing = [claim.claim_id for claim in self.claims if not claim.evidence_spans]
        if missing:
            raise ValueError(f"accepted claims must have evidence_spans: {missing}")
        return self


class ClaimReviewBundle(BaseModel):
    project_id: str
    target_stage: Literal["claim_extraction"] = "claim_extraction"
    reviews: list[ReviewResult]
    gate_decision: GateDecision
    created_at: str

