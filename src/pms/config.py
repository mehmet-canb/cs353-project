import logging
from pathlib import Path

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

logger = logging.getLogger(__name__)


class EnvironmentSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.prod", ".env.test"),
        env_file_encoding="utf-8",
    )

    # NOTE: Below code is needed because by default pydantic prioritizes environment
    #   variables instead of dotenvironment ones.
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: BaseSettings,
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return dotenv_settings, env_settings, init_settings, file_secret_settings

    project_root: Path
    secret_key: str
    db_name: str
    postgres_user: str
    postgres_password: str
    db_host: str
    db_port: str


env_settings = EnvironmentSettings()

if __name__ == "__main__":
    logger.warning(env_settings.model_dump_json())
