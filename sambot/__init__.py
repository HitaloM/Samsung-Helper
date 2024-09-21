# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
from contextlib import suppress
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from sambot.config import config
from sambot.utils.logging import log
from sambot.utils.systools import ShellExceptionError, shell_run

commit_count = "None"
commit_hash = "None"
with suppress(ShellExceptionError):
    commit_count = asyncio.run(shell_run("git rev-list --count HEAD"))
    commit_hash = asyncio.run(shell_run("git rev-parse --short HEAD"))

__version__ = f"{commit_hash} ({commit_count})"

log.info("Starting Samgung Helper Bot...", version=__version__)

app_dir = Path(__file__).parent.parent

bot = Bot(
    token=config.bot_token.get_secret_value(),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True),
)
dp = Dispatcher()
