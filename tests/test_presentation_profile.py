from pathlib import Path

from p2s_core.services.persona_style import (
    load_presentation_profile,
    validate_presentation_profile_package,
)


ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIR = ROOT / "p2s_core" / "presentation_profiles" / "presenter_first_default"


def test_load_presenter_first_default_profile():
    profile = load_presentation_profile(
        "presenter_first_default",
        ROOT / "p2s_core" / "presentation_profiles",
    )

    assert profile.profile_id == "presenter_first_default"
    assert profile.presenter_priority == "high"
    assert profile.require_asset_every_scene is False
    assert profile.asset_insertion_policy == "only_when_helpful"
    assert profile.default_background_mode == "static_clean"


def test_validate_presenter_first_default_package():
    result = validate_presentation_profile_package(PROFILE_DIR)

    assert result.valid
    assert result.errors == []
    assert (PROFILE_DIR / "layout_rules.md").exists()
    assert (PROFILE_DIR / "examples" / "presenter_only.md").exists()
    assert (PROFILE_DIR / "examples" / "presenter_with_overlay.md").exists()
    assert (PROFILE_DIR / "examples" / "asset_focus.md").exists()
