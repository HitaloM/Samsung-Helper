# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from typing import ClassVar

from pydantic import AnyHttpUrl, SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: SecretStr
    redis_host: str = "localhost"
    cors_bypass: str
    sentry_url: AnyHttpUrl | None = None
    sudoers: ClassVar[list[int]] = [918317361]
    logs_channel: int | None = None
    fw_channel: int | None = None

    class Config:
        env_file = "data/config.env"
        env_file_encoding = "utf-8"


config = Settings()  # type: ignore[arg-type]
