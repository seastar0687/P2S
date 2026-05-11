"""Service package for P2S MVP 0."""

from p2s_core.services.llm_service import LLMService, LLMServiceError
from p2s_core.services.code_version import capture_code_version
from p2s_core.services.persona_style import (
    PackageValidationResult,
    check_persona_style_compatibility,
    load_presentation_profile,
    load_persona,
    load_style,
    validate_presentation_profile_package,
    validate_presentation_profile_packages,
    validate_persona_package,
    validate_persona_packages,
    validate_style_package,
    validate_style_packages,
)
from p2s_core.services.persistence import load_state, list_revisions, save_state, snapshot
from p2s_core.services.paper_extraction import extract_text, run_extraction_stage
from p2s_core.services.claim_extraction import extract_claims, run_claim_extraction_stage
from p2s_core.services.narrative_planning import run_narrative_planning_stage
from p2s_core.services.presentation_planning import run_presentation_planning_stage
from p2s_core.services.llm_quality_rewrite import run_llm_quality_rewrite_stage
from p2s_core.services.asset_preparation import prepare_assets_for_project, run_asset_preparation_stage
from p2s_core.services.media_generation import run_asset_generation_stage, run_composition_stage
from p2s_core.services.media_quality import run_media_quality_check_stage

__all__ = [
    "LLMService",
    "LLMServiceError",
    "PackageValidationResult",
    "capture_code_version",
    "check_persona_style_compatibility",
    "extract_text",
    "extract_claims",
    "load_persona",
    "load_presentation_profile",
    "load_state",
    "load_style",
    "list_revisions",
    "save_state",
    "snapshot",
    "run_extraction_stage",
    "run_claim_extraction_stage",
    "run_narrative_planning_stage",
    "run_presentation_planning_stage",
    "run_llm_quality_rewrite_stage",
    "prepare_assets_for_project",
    "run_asset_preparation_stage",
    "run_asset_generation_stage",
    "run_composition_stage",
    "run_media_quality_check_stage",
    "validate_persona_package",
    "validate_persona_packages",
    "validate_presentation_profile_package",
    "validate_presentation_profile_packages",
    "validate_style_package",
    "validate_style_packages",
]
