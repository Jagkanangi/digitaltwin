import pytest
import os
from src.vo.settings import Settings

@pytest.fixture
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("CONNECTION__DB_HOST", "localhost")
    monkeypatch.setenv("CONNECTION__DB_PORT", "5432")
    monkeypatch.setenv("CONNECTION__DB_TYPE", "postgres")
    monkeypatch.setenv("CONNECTION__REDIS_HOST", "localhost")
    monkeypatch.setenv("CONNECTION__REDIS_PORT", "6379")
    monkeypatch.setenv("DB_RETRIEVAL__NN_COUNT", "3")
    monkeypatch.setenv("SYSTEM__ALLOWED_ORIGINS", "*")
    monkeypatch.setenv("SYSTEM__MODELS__CHUNKING_MODEL", "model1")
    monkeypatch.setenv("SYSTEM__MODELS__EMBEDDING_MODEL", "model2")
    monkeypatch.setenv("SYSTEM__MODELS__LLM_MODEL", "model3")
    monkeypatch.setenv("SYSTEM__LLM_SETTINGS__LLM_TEMPERATURE", "0.7")
    monkeypatch.setenv("SYSTEM__LLM_SETTINGS__LLM_MAX_TOKENS", "1024")
    monkeypatch.setenv("SYSTEM__LLM_SETTINGS__LLM_RAG_ENABLED", "True")
    monkeypatch.setenv("SYSTEM__LLM_INTENT_PROVIDER__HOST", "host")
    monkeypatch.setenv("SYSTEM__LLM_INTENT_PROVIDER__PROVIDER", "provider")
    monkeypatch.setenv("SYSTEM__LLM_INTENT_PROVIDER__MODEL", "model")
    monkeypatch.setenv("SYSTEM__CHUNK_SETTINGS__CHUNK_SIZE", "512")
    monkeypatch.setenv("SYSTEM__CHUNK_SETTINGS__CHUNK_OVERLAP", "50")
    monkeypatch.setenv("PERSONA_SETTINGS__PERSONA_TEMP", "0.5")
    monkeypatch.setenv("PERSONA_SETTINGS__CODE_EXPLANATION", "0.6")
    monkeypatch.setenv("PERSONA_SETTINGS__TECH_EXPLANATION", "0.7")
    monkeypatch.setenv("PERSONA_SETTINGS__PERSONA_COLLECTION_NAME", "collection")

def test_settings_loading(mock_env_vars):
    settings = Settings()

    assert settings.connection.db_host == "localhost"
    assert settings.connection.db_port == 5432
    assert settings.db_retrieval.nn_count == 3
    assert settings.system.models.llm_model == "model3"
    assert settings.persona_settings.persona_temp == 0.5
