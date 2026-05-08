from __future__ import annotations

import shutil
from pathlib import Path

from p2s_core.models import ProjectSource, ProjectState, default_stages
from p2s_core.pipelines.base import BasePipeline
from p2s_core.services.code_version import capture_code_version
from p2s_core.services import claim_extraction, llm_quality_rewrite, narrative_planning
from p2s_core.services import paper_extraction, persistence
from p2s_core.services import presentation_planning
from p2s_core.services.persona_style import load_persona, load_style


class PaperSummaryPipeline(BasePipeline):
    """MVP paper summary pipeline with setup and extraction only."""

    def __init__(
        self,
        personas_dir: str | Path = "p2s_core/personas",
        styles_dir: str | Path = "p2s_core/styles",
    ):
        self.personas_dir = Path(personas_dir)
        self.styles_dir = Path(styles_dir)

    def setup_project(
        self,
        pdf_path: str | Path,
        persona_id: str = "seina",
        style_id: str = "rigorous_science_short",
        project_id: str | None = None,
    ) -> ProjectState:
        source_pdf = Path(pdf_path)
        project_id = project_id or self._generate_project_id()
        project_dir = persistence.project_dir(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)

        copied_pdf = project_dir / "source.pdf"
        shutil.copy2(source_pdf, copied_pdf)

        persona = load_persona(persona_id, self.personas_dir)
        style = load_style(style_id, self.styles_dir)
        state = ProjectState(
            project_id=project_id,
            created_at=self.utc_now(),
            source=ProjectSource(pdf_path=str(copied_pdf)),
            persona=persona.model_dump(),
            style=style.model_dump(),
            stages=default_stages(),
        )
        persistence.save_state(state)
        return state

    def run_stage(self, project_id: str, stage_name: str, force: bool = False) -> ProjectState:
        state = persistence.load_state(project_id)
        self._ensure_current_stages(state)
        self.assert_stage_can_run(state, stage_name, force=force)

        if stage_name not in {
            "extraction",
            "claim_extraction",
            "narrative_planning",
            "presentation_planning",
            "llm_quality_rewrite",
        }:
            raise NotImplementedError("此 stage 將在 MVP 2+ 實作")

        persistence.snapshot(project_id)
        code_version = capture_code_version()
        stage = state.stages[stage_name]
        stage.code_version = code_version
        state.code_version = code_version
        stage.status = "running"
        stage.started_at = self.utc_now()
        stage.finished_at = None
        stage.error = None
        persistence.save_state(state)

        try:
            if stage_name == "extraction":
                state = paper_extraction.run_extraction_stage(state)
            elif stage_name == "claim_extraction":
                state = claim_extraction.run_claim_extraction_stage(state)
            elif stage_name == "narrative_planning":
                state = narrative_planning.run_narrative_planning_stage(state)
            elif stage_name == "presentation_planning":
                state = presentation_planning.run_presentation_planning_stage(state)
            else:
                state = llm_quality_rewrite.run_llm_quality_rewrite_stage(state)
            state.code_version = capture_code_version()
            state.stages[stage_name].finished_at = self.utc_now()
            persistence.save_state(state)
            return state
        except llm_quality_rewrite.RewriteGuardrailError as exc:
            state.code_version = capture_code_version()
            state.stages[stage_name].status = "rejected"
            state.stages[stage_name].finished_at = self.utc_now()
            state.stages[stage_name].error = str(exc)
            persistence.save_state(state)
            raise
        except Exception as exc:
            state.code_version = capture_code_version()
            state.stages[stage_name].status = "failed"
            state.stages[stage_name].finished_at = self.utc_now()
            state.stages[stage_name].error = str(exc)
            persistence.save_state(state)
            raise

    def _generate_project_id(self) -> str:
        return self.utc_now().replace(":", "").replace("-", "").split(".")[0]

    @staticmethod
    def _ensure_current_stages(state: ProjectState) -> None:
        for stage_name, stage in default_stages().items():
            state.stages.setdefault(stage_name, stage)
        if not getattr(state, "active_scene_source", None):
            state.active_scene_source = "scenes.json"
