from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="QA_", extra="ignore")

    database_url: str = "postgresql+psycopg://quote:quote@127.0.0.1:5432/quote_assistant"
    seed_demo_data: bool = False
    session_ttl_hours: int = 12
    demo_password_a: str = "change-me-a"
    demo_password_b: str = "change-me-b"

    # local = directory on disk (tests / local dev). oss = 阿里云 OSS (production).
    object_store_backend: str = "local"
    local_object_dir: str = "/tmp/quote-assistant-objects"
    public_base_url: str = ""
    object_sign_secret: str = "dev-object-sign-secret"
    signed_url_ttl_seconds: int = 300

    oss_access_key_id: str = ""
    oss_access_key_secret: str = ""
    oss_endpoint: str = ""
    oss_bucket: str = ""
