from __future__ import annotations

from pathlib import Path

import click

from p2s_core.pipelines import (
    PaperSummaryPipeline,
    PipelineError,
    StageAlreadyDoneError,
    StagePrerequisiteError,
)
from p2s_core.services import LLMServiceError
from p2s_core.services import persistence
from p2s_core.services.persona_style import validate_persona_packages, validate_style_packages


@click.group()
def cli() -> None:
    """P2S MVP 0 command line interface."""


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--persona", "persona_id", default="seina", show_default=True)
@click.option("--style", "style_id", default="rigorous_science_short", show_default=True)
@click.option("--id", "project_id", default=None)
def init(pdf_path: Path, persona_id: str, style_id: str, project_id: str | None) -> None:
    pipeline = PaperSummaryPipeline()
    state = pipeline.setup_project(
        pdf_path=pdf_path,
        persona_id=persona_id,
        style_id=style_id,
        project_id=project_id,
    )
    project_dir = persistence.project_dir(state.project_id)

    click.echo(f"Created project: {state.project_id}")
    click.echo(f"  -> {project_dir}")
    click.echo(f"  -> persona: {state.persona['persona_id']}")
    click.echo(f"  -> style: {state.style['style_id']}")


@cli.command()
@click.option("--stage", "stage_name", required=True)
@click.option("--project", "project_id", default=None)
@click.option("--force", is_flag=True, default=False)
def run(stage_name: str, project_id: str | None, force: bool) -> None:
    project_id = _resolve_project_id(project_id)
    pipeline = PaperSummaryPipeline()

    try:
        state = pipeline.run_stage(project_id, stage_name, force=force)
    except NotImplementedError as exc:
        raise click.ClickException(str(exc)) from exc
    except (PipelineError, FileNotFoundError, ValueError, LLMServiceError) as exc:
        raise click.ClickException(str(exc)) from exc

    stage = state.stages[stage_name]
    click.echo(f"Running stage: {stage_name}")
    click.echo(f"  -> status: {stage.status}")
    for output_path in stage.output_paths:
        click.echo(f"  -> {output_path}")


@cli.command()
@click.option("--project", "project_id", default=None)
def status(project_id: str | None) -> None:
    project_id = _resolve_project_id(project_id)
    state = persistence.load_state(project_id)

    click.echo(f"Project: {state.project_id}")
    click.echo(f"Persona: {state.persona.get('persona_id')} ({state.persona.get('version')})")
    click.echo(f"Style:   {state.style.get('style_id')} ({state.style.get('version')})")
    click.echo("")
    click.echo("Stages:")
    for stage_name, stage in state.stages.items():
        suffix = ""
        if stage.finished_at:
            suffix = f" ({stage.finished_at})"
        click.echo(f"  {stage_name:<22} {stage.status}{suffix}")


@cli.command("validate-personas")
def validate_personas_command() -> None:
    results = validate_persona_packages()
    _emit_validation_results(results)


@cli.command("validate-styles")
def validate_styles_command() -> None:
    results = validate_style_packages()
    _emit_validation_results(results)


def _emit_validation_results(results) -> None:
    has_error = False
    for result in results:
        if result.valid:
            click.echo(f"OK {result.path}: valid")
        else:
            has_error = True
            click.echo(f"FAIL {result.path}: invalid")
            for error in result.errors:
                click.echo(f"  - {error}")

    if has_error:
        raise click.ClickException("validation failed")


def _resolve_project_id(project_id: str | None) -> str:
    if project_id:
        return project_id

    candidates = [
        path
        for path in persistence.RUNS_DIR.iterdir()
        if path.is_dir() and (path / persistence.STATE_FILENAME).exists()
    ] if persistence.RUNS_DIR.exists() else []

    if not candidates:
        raise click.ClickException("No project specified and no project_state.json found under runs/.")

    latest = max(candidates, key=lambda path: (path / persistence.STATE_FILENAME).stat().st_mtime)
    return latest.name


if __name__ == "__main__":
    cli()
