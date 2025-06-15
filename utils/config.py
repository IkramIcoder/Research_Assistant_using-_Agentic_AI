# utils/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    AGENT_TEMPERATURE: float = 0.3
    MAX_ITERATIONS: int = 10

    class Config:
        env_file = ".env"

settings = Settings()