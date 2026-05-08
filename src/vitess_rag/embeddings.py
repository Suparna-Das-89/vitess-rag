import os

from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class BlabladorEmbeddingFunction(EmbeddingFunction[Documents]):
    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        self.model_name = model_name or os.getenv("BLABLADOR_EMBEDDING_MODEL", "alias-embeddings")
        self.api_key = api_key or os.getenv("BLABLADOR_API_KEY")
        self.base_url = base_url or os.getenv("BLABLADOR_BASE_URL")

        if not self.api_key or not self.base_url:
            raise ValueError("Missing BLABLADOR_API_KEY or BLABLADOR_BASE_URL.")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def __call__(self, input: Documents) -> Embeddings:
        response = self.client.embeddings.create(
            model=self.model_name,
            input=list(input),
        )
        return [item.embedding for item in response.data]

    @staticmethod
    def name() -> str:
        return "blablador-embedding"

    def get_config(self) -> dict:
        return {"model_name": self.model_name}

    @staticmethod
    def build_from_config(config: dict) -> "BlabladorEmbeddingFunction":
        return BlabladorEmbeddingFunction(
            model_name=config.get("model_name", "alias-embeddings")
        )
