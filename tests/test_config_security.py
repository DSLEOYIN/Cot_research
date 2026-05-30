from app_config import get_config
from pathlib import Path


def test_dify_is_disabled_without_explicit_credentials(monkeypatch):
    monkeypatch.delenv("DIFY_API_KEY", raising=False)
    monkeypatch.delenv("DIFY_DATASET_ID", raising=False)
    monkeypatch.delenv("DIFY_BASE_URL", raising=False)

    config = get_config()

    assert config.dify.enabled is False
    assert config.dify.api_key is None
    assert config.dify.dataset_id is None


def test_repository_does_not_contain_known_real_secrets():
    root_dir = Path(__file__).resolve().parents[1]
    sensitive_values = [
        "dataset-S5L6smkj8ovnSz8rMl5DZUvj",
        "^Dskj@Model1",
    ]

    text_files = [
        *root_dir.glob("*.py"),
        *root_dir.glob("mcps/*.py"),
        *root_dir.glob("skills/*.py"),
        *root_dir.glob("doc/*.md"),
        *root_dir.glob("history/*.md"),
        *root_dir.glob("qa/*.md"),
        root_dir / ".env.example",
    ]

    offenders = []
    for path in text_files:
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        for value in sensitive_values:
            if value in content:
                offenders.append(str(path.relative_to(root_dir)))

    assert offenders == []
