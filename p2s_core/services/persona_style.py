from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import ValidationError

from p2s_core.models import PersonaProfile, PresentationProfile, StyleProfile


@dataclass(frozen=True)
class PackageValidationResult:
    path: Path
    valid: bool
    errors: list[str]


def load_persona(persona_id: str, personas_dir: str | Path = "p2s_core/personas") -> PersonaProfile:
    package_dir = Path(personas_dir) / persona_id
    return PersonaProfile.model_validate(_read_yaml(package_dir / "persona.yaml"))


def load_style(style_id: str, styles_dir: str | Path = "p2s_core/styles") -> StyleProfile:
    package_dir = Path(styles_dir) / style_id
    return StyleProfile.model_validate(_read_yaml(package_dir / "style.yaml"))


def load_presentation_profile(
    profile_id: str = "presenter_first_default",
    profiles_dir: str | Path = "p2s_core/presentation_profiles",
) -> PresentationProfile:
    package_dir = Path(profiles_dir) / profile_id
    return PresentationProfile.model_validate(_read_yaml(package_dir / "presentation.yaml"))


def validate_persona_package(package_dir: str | Path) -> PackageValidationResult:
    package_dir = Path(package_dir)
    errors = _validate_required_paths(
        package_dir,
        ["persona.yaml", "prompt_profile.md", "speaking_rules.md", "examples"],
    )
    if not errors:
        try:
            PersonaProfile.model_validate(_read_yaml(package_dir / "persona.yaml"))
        except (ValidationError, OSError, yaml.YAMLError) as exc:
            errors.append(str(exc))

    return PackageValidationResult(path=package_dir / "persona.yaml", valid=not errors, errors=errors)


def validate_style_package(package_dir: str | Path) -> PackageValidationResult:
    package_dir = Path(package_dir)
    errors = _validate_required_paths(
        package_dir,
        ["style.yaml", "prompt_guide.md", "forbidden_phrases.txt", "examples"],
    )
    if not errors:
        try:
            StyleProfile.model_validate(_read_yaml(package_dir / "style.yaml"))
        except (ValidationError, OSError, yaml.YAMLError) as exc:
            errors.append(str(exc))

    return PackageValidationResult(path=package_dir / "style.yaml", valid=not errors, errors=errors)


def validate_presentation_profile_package(package_dir: str | Path) -> PackageValidationResult:
    package_dir = Path(package_dir)
    errors = _validate_required_paths(
        package_dir,
        [
            "presentation.yaml",
            "layout_rules.md",
            "examples/presenter_only.md",
            "examples/presenter_with_overlay.md",
            "examples/asset_focus.md",
        ],
    )
    if not errors:
        try:
            PresentationProfile.model_validate(_read_yaml(package_dir / "presentation.yaml"))
        except (ValidationError, OSError, yaml.YAMLError) as exc:
            errors.append(str(exc))

    return PackageValidationResult(path=package_dir / "presentation.yaml", valid=not errors, errors=errors)


def validate_persona_packages(personas_dir: str | Path = "p2s_core/personas") -> list[PackageValidationResult]:
    return [
        validate_persona_package(path.parent)
        for path in sorted(Path(personas_dir).glob("*/persona.yaml"))
    ]


def validate_style_packages(styles_dir: str | Path = "p2s_core/styles") -> list[PackageValidationResult]:
    return [
        validate_style_package(path.parent)
        for path in sorted(Path(styles_dir).glob("*/style.yaml"))
    ]


def validate_presentation_profile_packages(
    profiles_dir: str | Path = "p2s_core/presentation_profiles",
) -> list[PackageValidationResult]:
    return [
        validate_presentation_profile_package(path.parent)
        for path in sorted(Path(profiles_dir).glob("*/presentation.yaml"))
    ]


def check_persona_style_compatibility(
    persona: PersonaProfile,
    style: StyleProfile,
) -> list[str]:
    warnings: list[str] = []
    dramatic_keywords = ["dramatic", "overexcited", "clickbait", "誇張", "戲劇化"]

    if style.rigor_level >= 4:
        text = " ".join(persona.personality_traits + [persona.speaking_style_summary]).lower()
        if any(keyword.lower() in text for keyword in dramatic_keywords):
            warnings.append("high-rigor style may conflict with dramatic persona tone")

    return warnings


def _read_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def _validate_required_paths(package_dir: Path, required_paths: list[str]) -> list[str]:
    errors: list[str] = []
    for relative_path in required_paths:
        path = package_dir / relative_path
        if not path.exists():
            errors.append(f"missing required path: {relative_path}")
    return errors
