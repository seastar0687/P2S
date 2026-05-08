from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from p2s_core.models import ClaimExtractionResult, NarrativeArcItem, NarrativePlan, PaperClaim, ProjectState
import p2s_core.services.persistence as persistence


RISK_FLAGS_TO_EXCLUDE = {"unsupported", "missing_evidence"}


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def run_narrative_planning_stage(state: ProjectState) -> ProjectState:
    project_dir = persistence.project_dir(state.project_id)
    claims = load_project_claims(state, project_dir)
    plan = build_narrative_plan(state, claims)
    output_path = project_dir / "narrative_plan.json"
    output_path.write_text(plan.model_dump_json(indent=2), encoding="utf-8")

    state.narrative_plan = plan.model_dump()
    stage = state.stages["narrative_planning"]
    stage.status = "done"
    stage.output_paths = ["narrative_plan.json"]
    return state


def load_project_claims(state: ProjectState, project_dir: Path | None = None) -> list[PaperClaim]:
    if state.claims:
        return state.claims

    project_dir = project_dir or persistence.project_dir(state.project_id)
    claims_path = project_dir / "claims.json"
    if not claims_path.exists():
        raise FileNotFoundError(f"claims.json not found: {claims_path}")

    payload = claims_path.read_text(encoding="utf-8")
    try:
        return ClaimExtractionResult.model_validate_json(payload).claims
    except ValueError:
        data = json.loads(payload)
        raw_claims = data.get("claims", data if isinstance(data, list) else [])
        return [PaperClaim.model_validate(item) for item in raw_claims]


def build_narrative_plan(state: ProjectState, claims: list[PaperClaim]) -> NarrativePlan:
    accepted = _accepted_claims(claims)
    if not accepted:
        raise ValueError("Cannot build narrative plan: no accepted grounded claims found.")

    selected = _select_claims(accepted, max_claims=6)
    selected_ids = [claim.claim_id for claim in selected]
    omitted_ids = [claim.claim_id for claim in accepted if claim.claim_id not in selected_ids]

    return NarrativePlan(
        project_id=state.project_id,
        target_duration_sec=state.settings.target_duration_sec,
        language=state.settings.language,
        audience=state.settings.target_audience,
        selected_claim_ids=selected_ids,
        narrative_arc=_build_arc(selected),
        omitted_claim_ids=omitted_ids,
        rationale=(
            "Deterministic MVP2A plan: select high-importance grounded claims "
            "and map each beat to a clear short-form presentation purpose."
        ),
        risk_flags=[],
        created_at=utc_now(),
    )


def _accepted_claims(claims: list[PaperClaim]) -> list[PaperClaim]:
    return [
        claim
        for claim in claims
        if claim.evidence_spans and not (set(claim.risk_flags) & RISK_FLAGS_TO_EXCLUDE)
    ]


def _select_claims(claims: list[PaperClaim], max_claims: int) -> list[PaperClaim]:
    ordered = sorted(claims, key=lambda claim: (-claim.importance, claim.claim_id))
    selected: list[PaperClaim] = []

    for claim_type_group in (
        ("problem", "background"),
        ("method", "contribution"),
        ("result",),
        ("limitation",),
    ):
        candidate = next(
            (claim for claim in ordered if claim.claim_type in claim_type_group and claim not in selected),
            None,
        )
        if candidate:
            selected.append(candidate)

    for claim in ordered:
        if len(selected) >= max_claims:
            break
        if claim not in selected:
            selected.append(claim)

    important_limitation = next(
        (claim for claim in ordered if claim.claim_type == "limitation" and claim.importance >= 4),
        None,
    )
    if important_limitation and important_limitation not in selected:
        if len(selected) >= max_claims:
            selected[-1] = important_limitation
        else:
            selected.append(important_limitation)

    return selected


def _build_arc(claims: list[PaperClaim]) -> list[NarrativeArcItem]:
    arc: list[NarrativeArcItem] = []
    for index, claim in enumerate(claims):
        purpose = _purpose_for_claim(index, claim)
        arc.append(
            NarrativeArcItem(
                purpose=purpose,
                claim_ids=[claim.claim_id],
                intent=_intent_for_purpose(purpose),
            )
        )

    if not any(item.purpose == "takeaway" for item in arc):
        arc.append(
            NarrativeArcItem(
                purpose="takeaway",
                claim_ids=[claims[0].claim_id],
                intent="收束為可記住但仍受 claim 支持的 takeaway",
            )
        )
    return arc


def _purpose_for_claim(index: int, claim: PaperClaim):
    if index == 0:
        return "hook"
    if claim.claim_type in {"problem", "background"}:
        return "problem"
    if claim.claim_type in {"method", "contribution"}:
        return "method"
    if claim.claim_type == "result":
        return "result"
    if claim.claim_type == "limitation":
        return "limitation"
    return "method"


def _intent_for_purpose(purpose: str) -> str:
    return {
        "hook": "用受支持的研究重點開場，不誇大",
        "problem": "說明研究問題或背景動機",
        "method": "用一般科學觀眾可理解的方式壓縮方法或貢獻",
        "result": "說明關鍵結果，維持和原文 evidence 對齊",
        "limitation": "保留限制或適用範圍，避免把研究說得太滿",
        "takeaway": "收束為可記住但仍受 claim 支持的 takeaway",
        "transition": "連接前後段落，不新增事實主張",
    }[purpose]
