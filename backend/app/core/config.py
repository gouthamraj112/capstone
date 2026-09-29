from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://mongo:27017"
    database_name: str = "smart_grid"
    frontend_url: str = "http://frontend:80"
    llm_provider: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    model_config = SettingsConfigDict(env_file=(".env", "backend/.env"), extra="ignore")


settings = Settings()
