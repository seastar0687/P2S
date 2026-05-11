from __future__ import annotations

from datetime import UTC, datetime

from p2s_core.models import ProjectState


class PipelineError(Exception):
    """Base exception for MVP pipeline failures."""


class StageAlreadyDoneError(PipelineError):
    """Raised when rerunning a completed stage without force."""


class StagePrerequisiteError(PipelineError):
    """Raised when a stage dependency is not complete."""


class BasePipeline:
    stage_order = (
        "extraction",
        "claim_extraction",
        "narrative_planning",
        "presentation_planning",
        "llm_quality_rewrite",
        "asset_preparation",
        "asset_generation",
        "composition",
        "final_review",
    )

    def assert_stage_can_run(self, state: ProjectState, stage_name: str, force: bool = False) -> None:
        if stage_name not in self.stage_order:
            raise ValueError(f"Unknown stage: {stage_name}")

        stage = state.stages[stage_name]
        if stage.status == "done" and not force:
            raise StageAlreadyDoneError(f"Stage already done: {stage_name}. Use force=True to rerun.")

        for prerequisite in self._prerequisites_for(stage_name):
            if state.stages[prerequisite].status != "done":
                raise StagePrerequisiteError(
                    f"Stage {stage_name} requires {prerequisite} to be done first."
                )

    def _prerequisites_for(self, stage_name: str) -> tuple[str, ...]:
        if stage_name == "asset_preparation":
            return (
                "extraction",
                "claim_extraction",
                "narrative_planning",
                "presentation_planning",
            )
        stage_index = self.stage_order.index(stage_name)
        return self.stage_order[:stage_index]

    @staticmethod
    def utc_now() -> str:
        return datetime.now(UTC).isoformat()

    def run_stage(self, project_id: str, stage_name: str, force: bool = False) -> ProjectState:
        raise NotImplementedError
