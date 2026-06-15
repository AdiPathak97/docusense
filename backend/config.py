from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM chat provider
    llm_provider: Literal["claude", "azure_openai", "openai"] = "claude"

    # Claude
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"

    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment_chat: str = "gpt-4o"
    azure_openai_deployment_embedding: str = "text-embedding-ada-002"
    azure_openai_api_version: str = "2025-04-01-preview"

    # OpenAI
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o"

    # Embedding provider (claude has no embeddings API — always set independently)
    embedding_provider: Literal["azure_openai", "openai"] = "openai"

    # Infrastructure
    database_url: str = "postgresql+asyncpg://docusense:docusense@localhost:5432/docusense"
    chroma_host: str = "localhost"
    chroma_port: int = 8000

    # Agent tuning
    top_k_retrieval: int = 5
    relevance_threshold: float = 0.6

    # Dev
    use_mock_llm: bool = False

    # Logging
    log_level: str = "INFO"   # DEBUG | INFO | WARNING | ERROR | CRITICAL
    log_format: str = "plain"  # plain | json


settings = Settings()
