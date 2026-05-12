from __future__ import annotations

import re
from pathlib import Path

from p2s_core.models import FinalGateDecision, FinalReviewBundle


def next_review_paths(run_dir: Path) -> tuple[Path, Path, str]:
    reviews_dir = run_dir / "reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)
    revision = _next_revision(reviews_dir)
    review_id = f"final_review_rev{revision:03d}"
    return (
        reviews_dir / f"final_review_rev{revision:03d}.json",
        reviews_dir / f"final_gate_decision_rev{revision:03d}.json",
        review_id,
    )


def write_final_review_outputs(
    run_dir: Path,
    bundle: FinalReviewBundle,
    decision: FinalGateDecision,
) -> tuple[str, str]:
    review_path = run_dir / "reviews" / f"{bundle.review_id}.json"
    gate_path = run_dir / "reviews" / f"final_gate_decision_{bundle.review_id.removeprefix('final_review_')}.json"
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(bundle.model_dump_json(indent=2), encoding="utf-8")
    gate_path.write_text(decision.model_dump_json(indent=2), encoding="utf-8")
    return (str(review_path.relative_to(run_dir)), str(gate_path.relative_to(run_dir)))


def _next_revision(reviews_dir: Path) -> int:
    revisions: list[int] = []
    for path in reviews_dir.glob("final_review_rev*.json"):
        match = re.fullmatch(r"final_review_rev(\d{3})\.json", path.name)
        if match:
            revisions.append(int(match.group(1)))
    return max(revisions, default=0) + 1
