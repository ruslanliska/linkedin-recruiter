from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

__all__ = [
    'settings',
]


class AppSettings(BaseSettings):
    OPENAI_API_KEY: str = Field(default='')

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent / '.env',
        extra='ignore',
    )


settings = AppSettings()
