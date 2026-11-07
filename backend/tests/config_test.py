
from app.core.config import Settings


def test_settings_use_default_values():
    settings = Settings(
        _env_file=None,
        secret_key="test-secret-key",
        database_url="sqlite:///./test.db",
    )

    assert settings.app_name == "SpendWise AI"
    assert settings.app_version == "0.1.0"
    assert settings.environment == "development"
    assert settings.debug is True


def test_settings_read_environment_variables(monkeypatch):
    monkeypatch.setenv("APP_NAME", "SpendWise Test")
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")

    settings = Settings(_env_file=None)

    assert settings.app_name == "SpendWise Test"
    assert settings.environment == "testing"
    assert settings.debug is False
    assert settings.secret_key == "test-secret-key"
    assert settings.database_url == "sqlite:///./test.db"
