from pathlib import Path

from p2s_core.config import load_config


ROOT = Path(__file__).resolve().parents[1]
TEST_CONFIG_DIR = ROOT / ".test_runs" / "config"


def test_load_config_reads_project_local_dotenv(monkeypatch):
    import shutil

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    if TEST_CONFIG_DIR.exists():
        shutil.rmtree(TEST_CONFIG_DIR)
    TEST_CONFIG_DIR.mkdir(parents=True)
    config_path = TEST_CONFIG_DIR / "config.yaml"
    env_path = TEST_CONFIG_DIR / ".env"

    config_path.write_text(
        "llm:\n  api_key: ${OPENAI_API_KEY}\n",
        encoding="utf-8",
    )
    env_path.write_text("OPENAI_API_KEY=sk-project-local\n", encoding="utf-8")

    config = load_config(config_path)

    assert config["llm"]["api_key"] == "sk-project-local"
