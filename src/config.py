import sys
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

__all__ = [
    'settings',
]


def get_env_path() -> Path:
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundled executable
        exe_path = Path(sys.executable).parent.parent
        env_path = exe_path / '.env'
    else:
        # If run as a normal script
        env_path = Path(__file__).parent.parent / '.env'
    return env_path


class AppSettings(BaseSettings):
    OPENAI_API_KEY: str = Field(default='ggg')
    CHECK: str = Field(default='check')
    DRIVER_PATH: str = Field(default=None)

    model_config = SettingsConfigDict(
        env_file=get_env_path(),
        extra='ignore',
    )


settings = AppSettings()
