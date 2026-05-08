from pathlib import Path

from p2s_core.models import PersonaProfile, StyleProfile
from p2s_core.services import (
    load_persona,
    load_style,
    validate_persona_package,
    validate_style_package,
)


ROOT = Path(__file__).resolve().parents[1]


def test_load_seina_persona():
    persona = load_persona("seina", ROOT / "p2s_core" / "personas")

    assert isinstance(persona, PersonaProfile)
    assert persona.persona_id == "seina"
    assert persona.name == "Seina"


def test_load_rigorous_science_short_style():
    style = load_style("rigorous_science_short", ROOT / "p2s_core" / "styles")

    assert isinstance(style, StyleProfile)
    assert style.style_id == "rigorous_science_short"
    assert style.rigor_level == 5


def test_persona_vrm_is_none_in_mvp():
    persona = load_persona("seina", ROOT / "p2s_core" / "personas")

    assert persona.vrm is None
    assert persona.visual_identity is None


def test_validate_seina_persona_package():
    result = validate_persona_package(ROOT / "p2s_core" / "personas" / "seina")

    assert result.valid is True
    assert result.errors == []


def test_validate_rigorous_science_short_style_package():
    result = validate_style_package(ROOT / "p2s_core" / "styles" / "rigorous_science_short")

    assert result.valid is True
    assert result.errors == []


def test_seina_mvp_reserved_directories_exist():
    persona_dir = ROOT / "p2s_core" / "personas" / "seina"

    assert (persona_dir / "voice" / "tts_profile.yaml").exists()
    assert (persona_dir / "voice" / "training_data").is_dir()
    assert (persona_dir / "voice" / "reference_audio").is_dir()
    assert (persona_dir / "vrm").is_dir()
    assert (persona_dir / "visual_refs").is_dir()
    assert (persona_dir / "review" / "persona_consistency_rubric.yaml").exists()


def test_rigorous_style_mvp_reserved_files_exist():
    style_dir = ROOT / "p2s_core" / "styles" / "rigorous_science_short"

    assert (style_dir / "examples" / "good_02.md").exists()
    assert (style_dir / "rubrics" / "script_style_rubric.yaml").exists()
    assert (style_dir / "rewrite_rules.yaml").exists()
    assert (style_dir / "structure.md").exists()
