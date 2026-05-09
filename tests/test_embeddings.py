import pytest

from vitess_rag.embeddings import BlabladorEmbeddingFunction


def test_embedding_function_requires_credentials(monkeypatch):
    monkeypatch.delenv("BLABLADOR_API_KEY", raising=False)
    monkeypatch.delenv("BLABLADOR_BASE_URL", raising=False)

    with pytest.raises(ValueError):
        BlabladorEmbeddingFunction()


def test_embedding_function_config(monkeypatch):
    monkeypatch.setenv("BLABLADOR_API_KEY", "fake-key")
    monkeypatch.setenv("BLABLADOR_BASE_URL", "https://example.com/v1")

    embedding_function = BlabladorEmbeddingFunction(model_name="test-model")

    assert embedding_function.name() == "blablador-embedding"
    assert embedding_function.get_config() == {"model_name": "test-model"}
