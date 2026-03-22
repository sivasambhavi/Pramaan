from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    neo4j_uri:      str = "bolt://localhost:7687"
    neo4j_user:     str = "neo4j"
    neo4j_password: str = "password"      # override in .env: NEO4J_PASSWORD=pramaa2026
    groq_api_key:   str = ""              # override in .env: GROQ_API_KEY=<key>
    pramaan_env:    str = "development"
    google_api_key: str = ""
    api_base_url:   str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
