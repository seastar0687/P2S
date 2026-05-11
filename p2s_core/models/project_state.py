from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from p2s_core.models.claim import PaperClaim
from p2s_core.models.review import ReviewResult


STAGE_NAMES = (
    "extraction",
    "claim_extraction",
    "narrative_planning",
    "presentation_planning",
    "llm_quality_rewrite",
    "asset_preparation",
    "asset_generation",
    "composition",
    "media_quality_check",
    "final_review",
)


class ProjectSource(BaseModel):
    pdf_path: str
    title: str | None = None
    authors: list[str] = Field(default_factory=list)
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
    normalized_text_md: str | None = None
    sections_path: str | None = None
    figures_path: str | None = None
    tables_path: str | None = None
    evidence_match_report_path: str | None = None
    sections: list[dict] = Field(default_factory=list)
    figures: list[dict] = Field(default_factory=list)
    tables: list[dict] = Field(default_factory=list)
    quality_report: dict = Field(default_factory=dict)


class CodeVersion(BaseModel):
    commit: str | None = None
    branch: str | None = None
    dirty: bool | None = None
    captured_at: str
    source: Literal["git", "unknown"] = "git"


class StageState(BaseModel):
    status: Literal["pending", "running", "done", "failed", "needs_review", "rejected"] = "pending"
    started_at: str | None = None
    finished_at: str | None = None
    output_paths: list[str] = Field(default_factory=list)
    error: str | None = None
    revision_count: int = 0
    code_version: CodeVersion | None = None


class ProjectState(BaseModel):
    project_id: str
    created_at: str
    source: ProjectSource
    settings: ProjectSettings = Field(default_factory=ProjectSettings)
    persona: dict
    style: dict
    extraction: ExtractionState = Field(default_factory=ExtractionState)
    claims: list[PaperClaim] = Field(default_factory=list)
    narrative_plan: dict = Field(default_factory=dict)
    presentation_plan: dict = Field(default_factory=dict)
    active_scene_source: str = "scenes.json"
    asset_plan: dict = Field(default_factory=dict)
    script: dict = Field(
        default_factory=lambda: {
            "target_duration": 60,
            "audience": "general_science",
            "scenes": [],
        }
    )
    storyboard: dict = Field(default_factory=lambda: {"frames": []})
    assets: dict = Field(default_factory=lambda: {"images": [], "audio": [], "segments": []})
    reviews: list[ReviewResult] = Field(default_factory=list)
    revision_history: list[dict] = Field(default_factory=list)
    code_version: CodeVersion | None = None
    final_video: dict = Field(default_factory=lambda: {"path": None, "status": "draft"})
    stages: dict[str, StageState]

    @model_validator(mode="after")
    def ensure_current_stage_contract(self) -> "ProjectState":
        current = self.stages or {}
        ordered = {
            stage_name: current.get(stage_name, StageState())
            for stage_name in STAGE_NAMES
        }
        for stage_name, stage in current.items():
            if stage_name not in ordered:
                ordered[stage_name] = stage
        self.stages = ordered
        if not self.active_scene_source:
            self.active_scene_source = "scenes.json"
        return self


def default_stages() -> dict[str, StageState]:
    return {stage_name: StageState() for stage_name in STAGE_NAMES}
