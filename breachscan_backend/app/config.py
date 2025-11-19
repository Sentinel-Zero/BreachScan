from pydantic import BaseSettings


class Settings(BaseSettings):
    tenable_access_key: str | None = None
    tenable_secret_key: str | None = None
    tenable_base_url: str = "https://cloud.tenable.com"  # Tenable.io default

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
