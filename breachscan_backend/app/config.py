try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback if dependency not installed; raise clear error.
    raise ImportError("pydantic-settings is required. Install with 'pip install pydantic-settings'.")


class Settings(BaseSettings):
    # Tenable (future real integration)
    tenable_access_key: str | None = None
    tenable_secret_key: str | None = None
    tenable_base_url: str = "https://cloud.tenable.com"  # Tenable.io default

    # App runtime
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "info"

    # Scheduling / expansion
    schedule_expansion_limit: int = 4096

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
