from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    api_key: str
    data_dir: str
    nltk_disable_import_security: str | int | bool = True
    python_safepath: str | int | bool = True

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        extra="ignore",
    )

settings = Settings()