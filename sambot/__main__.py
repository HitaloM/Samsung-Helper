# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
import datetime
from contextlib import suppress

import aiocron
import sentry_sdk
import uvloop
from aiogram import __version__ as aiogram_version
from aiogram.exceptions import TelegramForbiddenError
from aiosqlite import __version__ as aiosqlite_version

from sambot import __version__ as sambot_version
from sambot import bot, config, dp
from sambot.database import create_tables, run_vacuum
from sambot.database.devices import Devices
from sambot.database.firmware import Firmwares
from sambot.handlers import doas
from sambot.utils.devices import sync_devices
from sambot.utils.logging import log
from sambot.utils.notify import sync_firmwares


async def main():
    if config.sentry_url:
        log.info("Starting sentry.io integraion.")

        sentry_sdk.init(str(config.sentry_url))

    await create_tables()
    dbs = [
        Devices().db_path,
        Firmwares().db_path,
    ]
    for db in dbs:
        await run_vacuum(db)

    dp.include_router(doas.router)

    aiocron.crontab(
        "0 */6 * * *",
        func=sync_firmwares,
        loop=asyncio.get_event_loop(),
        tz=datetime.UTC,
    )
    aiocron.crontab(
        "0 0 1 * *",
        func=sync_devices,
        loop=asyncio.get_event_loop(),
        tz=datetime.UTC,
    )

    with suppress(TelegramForbiddenError):
        if config.logs_channel:
            log.info("Sending startup notification.")
            await bot.send_message(
                config.logs_channel,
                text=(
                    "<b>Samsung Helper is up and running!</b>\n\n"
                    f"<b>Version:</b> <code>{sambot_version}</code>\n"
                    f"<b>AIOgram version:</b> <code>{aiogram_version}</code>\n"
                    f"<b>AIOSQLite version:</b> <code>{aiosqlite_version}</code>"
                ),
            )

    # resolve used update types
    useful_updates = dp.resolve_used_update_types()
    await dp.start_polling(bot, allowed_updates=useful_updates)


if __name__ == "__main__":
    try:
        with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
            runner.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("Samsung Helper Bot stopped!")
