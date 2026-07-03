from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings


load_dotenv()


class Settings(BaseSettings):
    app_env: str = "development"
    secure_mode: bool = True
    hitl_mode: str = "console"

    llm_provider: str = "groq"
    llm_model: str = "deepseek-r1-distill-llama-70b"
    llm_api_key: str = Field(default="replace-me")
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_temperature: float = 0.1

    astra_db_api_endpoint: str = ""
    astra_db_application_token: str = ""
    astra_db_keyspace: str = "default_keyspace"
    astra_kg_collection: str = "logistics_knowledge_graph"

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "incident_logistics_ai"
    mongodb_monitoring_collection: str = "monitoring_events"

    max_input_chars: int = 2500
    max_context_chars: int = 8000
    toxicity_threshold: float = 0.75
    hallucination_min_groundedness: float = 0.55
    max_estimated_cost_usd: float = 0.15

    business_dashboard_port: int = 8501
    monitoring_dashboard_port: int = 8502


ROOT_DIR = Path(__file__).resolve().parents[2]
CORPUS_DIR = ROOT_DIR / "data" / "corpus"
REPORTS_DIR = ROOT_DIR / "reports"
SCHEMA_PATH = ROOT_DIR / "schemas" / "incident_response.schema.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
