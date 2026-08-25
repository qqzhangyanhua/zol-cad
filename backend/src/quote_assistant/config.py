from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="QA_", extra="ignore")

    database_url: str = "postgresql+psycopg://quote:quote@127.0.0.1:5432/quote_assistant"
    seed_demo_data: bool = False
    session_ttl_hours: int = 12
    demo_password_a: str = "change-me-a"
    demo_password_b: str = "change-me-b"
