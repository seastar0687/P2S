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
from p2s_core.services.harden1_smoke import run_harden1_smoke_set
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
    if stage_name == "asset_preparation" and state.asset_plan:
        quality_report = state.asset_plan.get("quality_report", {})
        click.echo(f"  -> scene_source: {state.asset_plan.get('scene_source')}")
        click.echo(f"  -> scene_count: {quality_report.get('scene_count')}")
        click.echo(f"  -> warnings: {len(quality_report.get('warnings', []))}")
        for warning in quality_report.get("warnings", []):
            click.echo(f"     warning: {warning}")
    if stage_name == "composition" and state.final_video.get("path"):
        click.echo(f"  -> final_video: {state.final_video.get('path')}")
    if stage_name == "media_quality_check":
        report_path = persistence.project_dir(project_id) / "media_quality_report.json"
        if report_path.exists():
            import json

            report = json.loads(report_path.read_text(encoding="utf-8"))
            click.echo(f"  -> pass_gate: {report.get('pass_gate')}")
            click.echo(f"  -> blocking_issues: {len(report.get('blocking_issues', []))}")
            click.echo(f"  -> warnings: {len(report.get('warnings', []))}")


@cli.command()
@click.option("--project", "project_id", default=None)
def status(project_id: str | None) -> None:
    project_id = _resolve_project_id(project_id)
    state = persistence.load_state(project_id)

    click.echo(f"Project: {state.project_id}")
    click.echo(f"Persona: {state.persona.get('persona_id')} ({state.persona.get('version')})")
    click.echo(f"Style:   {state.style.get('style_id')} ({state.style.get('version')})")
    click.echo(f"Project code version: {_format_code_version(state.code_version)}")
    click.echo("")
    click.echo("Stages:")
    for stage_name, stage in state.stages.items():
        suffix = ""
        if stage.finished_at:
            suffix = f" ({stage.finished_at})"
        click.echo(f"  {stage_name:<22} {stage.status:<12} {_format_code_version(stage.code_version)}{suffix}")


@cli.group()
def smoke() -> None:
    """Smoke-test fixture sets."""


@smoke.command("real-papers")
@click.option("--set", "smoke_set", default="harden1", show_default=True)
def smoke_real_papers(smoke_set: str) -> None:
    if smoke_set != "harden1":
        raise click.ClickException(f"Unknown smoke set: {smoke_set}")
    try:
        reports = run_harden1_smoke_set()
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Ran HARDEN-1 smoke set: {len(reports)} paper(s)")
    for report in reports:
        click.echo(
            f"  -> {report.project_id}: {report.extraction_quality.quality_level}, "
            f"warnings={len(report.key_warnings)}"
        )


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


def _format_code_version(code_version) -> str:
    if code_version is None:
        return "-"
    if code_version.source != "git":
        return "unknown"
    commit = code_version.commit or "-"
    branch = code_version.branch or "-"
    clean_state = "dirty" if code_version.dirty else "clean"
    return f"{commit} {branch} {clean_state}"


if __name__ == "__main__":
    cli()
