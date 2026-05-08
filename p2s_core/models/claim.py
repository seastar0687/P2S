from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from p2s_core.models.common import EvidenceSpan


class PaperClaim(BaseModel):
    claim_id: str
    claim_text: str
    claim_type: Literal[
        "problem",
        "method",
        "result",
        "limitation",
        "contribution",
        "background",
    ]
    source_section: str
    evidence_spans: list[EvidenceSpan]
    certainty: Literal["explicit", "inferred", "weak"]
    importance: int
    risk_flags: list[Literal[
        "unsupported",
        "overhyped",
        "missing_evidence",
        "weak_evidence",
        "ambiguous",
        "too_broad",
    ]] = Field(default_factory=list)
