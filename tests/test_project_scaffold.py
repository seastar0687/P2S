from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_package_imports():
    import p2s_core
    import p2s_core.cli
    import p2s_core.config

    assert p2s_core.__version__ == "0.1.0"


def test_config_yaml_is_readable():
    config_path = ROOT / "config.yaml"

    assert config_path.exists()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert set(config) >= {"llm", "paths", "extraction"}


def test_persona_and_style_placeholders_exist():
    persona_dir = ROOT / "p2s_core" / "personas" / "seina"
    style_dir = ROOT / "p2s_core" / "styles" / "rigorous_science_short"

    assert (persona_dir / "persona.yaml").exists()
    assert (persona_dir / "prompt_profile.md").exists()
    assert (persona_dir / "speaking_rules.md").exists()
    assert (persona_dir / "examples" / "short_explainer_01.md").exists()

    assert (style_dir / "style.yaml").exists()
    assert (style_dir / "prompt_guide.md").exists()
    assert (style_dir / "forbidden_phrases.txt").exists()
    assert (style_dir / "examples" / "good_01.md").exists()
    assert (style_dir / "examples" / "bad_overhyped.md").exists()
