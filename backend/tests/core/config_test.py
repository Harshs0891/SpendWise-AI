from app.core.config import Settings


def test_settings_accept_explicit_required_values():
    settings = Settings(
        _env_file=None,
        secret_key="unit-test-secret",
        database_url="sqlite:///./unit-test.db",
    )

    assert settings.app_name == "SpendWise AI"
    assert settings.app_version == "0.1.0"
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.secret_key == "unit-test-secret"
    assert settings.database_url == "sqlite:///./unit-test.db"


def test_settings_read_environment_variables(monkeypatch):
    monkeypatch.setenv("APP_NAME", "SpendWise Test")
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("SECRET_KEY", "env-secret")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./env.db")

    settings = Settings(_env_file=None)

    assert settings.app_name == "SpendWise Test"
    assert settings.environment == "testing"
    assert settings.debug is False
    assert settings.secret_key == "env-secret"
    assert settings.database_url == "sqlite:///./env.db"
