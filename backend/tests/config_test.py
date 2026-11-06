from app.core.config import Settings


def test_settings_use_default_values():
    settings = Settings(_env_file=None)

    assert settings.app_name == "SpendWise AI"
    assert settings.app_version == "0.1.0"
    assert settings.environment == "development"
    assert settings.debug is True


def test_settings_read_environment_variables(monkeypatch):
    monkeypatch.setenv("APP_NAME", "SpendWise Test")
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("DEBUG", "false")

    settings = Settings(_env_file=None)

    assert settings.app_name == "SpendWise Test"
    assert settings.environment == "testing"
    assert settings.debug is False