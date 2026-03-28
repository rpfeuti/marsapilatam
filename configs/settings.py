"""
Bloomberg MARS API credentials loaded from environment variables or a .env file.

All domain constants (curve types, interpolation methods, etc.) live in
configs/curves_config.py so this module stays focused on credentials only.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Bloomberg MARS API credentials and connection settings.
    Values are read from environment variables or a .env file at project root.
    When credentials are absent the app automatically enters demo mode.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    bbg_client_id: str = Field(default="", description="Bloomberg Enterprise Console client ID")
    bbg_client_secret: str = Field(
        default="", description="Bloomberg Enterprise Console client secret (hex)"
    )
    bbg_uuid: int = Field(default=0, description="Bloomberg user UUID")
    bbg_host: str = Field(default="https://api.bloomberg.com", description="MARS API base URL")
    blpapi_host: str = Field(default="localhost", description="Bloomberg Desktop API host")
    blpapi_port: int = Field(default=8194,        description="Bloomberg Desktop API port")

    @property
    def demo_mode(self) -> bool:
        """True when Bloomberg credentials are not configured."""
        return not self.bbg_client_id or not self.bbg_client_secret or self.bbg_uuid == 0


settings = Settings()  # type: ignore[call-arg]
