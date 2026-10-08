from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    database_url: str = (
        "postgresql+asyncpg://app:app@127.0.0.1:5433/app"
    )
    
settings = Settings()