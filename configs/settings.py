"""
Bloomberg MARS API credentials loaded from environment variables or a .env file.

All domain constants (curve types, interpolation methods, etc.) live in
configs/curves_config.py so this module stays focused on credentials only.

Copyright 2026, Bloomberg Finance L.P.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to
deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:  The above
copyright notice and this permission notice shall be included in all copies
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
"""

from __future__ import annotations

from datetime import date

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

# Reference date used for all demo-mode displays.
# All demo_data/ snapshots were captured for this date.
DEMO_DATE = date(2026, 3, 27)
