import pytest

from vitess_rag.embeddings import BlabladorEmbeddingFunction


def test_embedding_function_requires_credentials(monkeypatch):
    monkeypatch.delenv("BLABLADOR_API_KEY", raising=False)
    monkeypatch.delenv("BLABLADOR_BASE_URL", raising=False)

    with pytest.raises(ValueError):
        BlabladorEmbeddingFunction()
