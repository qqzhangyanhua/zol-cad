from pydantic_settings import BaseSettings, SettingsConfigDict

UNSAFE_OBJECT_SIGN_SECRET = "dev-object-sign-secret"
UNSAFE_DEMO_PASSWORD_A = "change-me-a"
UNSAFE_DEMO_PASSWORD_B = "change-me-b"

_LOCAL_ENVS = frozenset({"local", "dev", "development", "test"})


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="QA_", extra="ignore")

    # local = placeholders allowed, cookie Secure off unless overridden.
    # production = refuse default secrets / insecure cookie and pin to one process.
    app_env: str = "local"

    database_url: str = "postgresql+psycopg://quote:quote@127.0.0.1:5432/quote_assistant"
    seed_demo_data: bool = False
    session_ttl_hours: int = 12
    demo_password_a: str = UNSAFE_DEMO_PASSWORD_A
    demo_password_b: str = UNSAFE_DEMO_PASSWORD_B

    # None = Secure unless local (HTTP localhost must opt out / inherit the default).
    session_cookie_secure: bool | None = None

    log_level: str = "INFO"

    # local = directory on disk (tests / local dev). oss = 阿里云 OSS (production).
    object_store_backend: str = "local"
    local_object_dir: str = "/tmp/quote-assistant-objects"
    public_base_url: str = ""
    object_sign_secret: str = UNSAFE_OBJECT_SIGN_SECRET
    signed_url_ttl_seconds: int = 300

    oss_access_key_id: str = ""
    oss_access_key_secret: str = ""
    oss_endpoint: str = ""
    oss_bucket: str = ""

    # fixture = seam-1 fake engine (default). vendor = unpaid skeleton; no live paid API.
    extraction_engine: str = "fixture"
    extraction_timeout_seconds: float = 60
    extraction_retry_count: int = 1
    extraction_cost_event_limit: int = 1000

    # thread = 分级 + 读图取数 run off the upload request (production; a real model takes
    # tens of seconds per drawing). inline = run before the response; 缝 1 uses this.
    part_drawing_processor: str = "thread"
    part_drawing_processor_workers: int = 4
    part_drawing_processor_queue_max: int = 64

    max_request_bytes: int = 256 * 1024 * 1024
    rate_limit_login_per_minute: int = 20
    rate_limit_upload_per_minute: int = 60

    @property
    def is_local(self) -> bool:
        return self.app_env.strip().lower() in _LOCAL_ENVS

    @property
    def effective_session_cookie_secure(self) -> bool:
        if self.session_cookie_secure is not None:
            return self.session_cookie_secure
        return not self.is_local


def validate_runtime_settings(settings: Settings) -> None:
    """Refuse to boot a non-local process that still has placeholder secrets or an insecure cookie."""
    if settings.is_local:
        return
    problems: list[str] = []
    if settings.object_sign_secret in {"", UNSAFE_OBJECT_SIGN_SECRET}:
        problems.append("QA_OBJECT_SIGN_SECRET 必须覆盖默认占位值")
    if settings.demo_password_a in {"", UNSAFE_DEMO_PASSWORD_A}:
        problems.append("QA_DEMO_PASSWORD_A 必须覆盖默认占位值")
    if settings.demo_password_b in {"", UNSAFE_DEMO_PASSWORD_B}:
        problems.append("QA_DEMO_PASSWORD_B 必须覆盖默认占位值")
    if not settings.effective_session_cookie_secure:
        problems.append("非本地环境必须启用 session cookie 的 Secure（QA_SESSION_COOKIE_SECURE）")
    if problems:
        raise RuntimeError("拒绝启动（非本地环境配置不安全）：" + "；".join(problems))
