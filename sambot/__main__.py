# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

import asyncio
import datetime
from contextlib import suppress

import aiocron
import sentry_sdk
from aiogram import __version__ as aiogram_version
from aiogram.exceptions import TelegramForbiddenError
from aiosqlite import __version__ as aiosqlite_version

from sambot import __version__ as sambot_version
from sambot import bot, config, dp, i18n
from sambot.database import create_tables
from sambot.handlers import doas, language, pm_menu, tools
from sambot.middlewares.acl import ACLMiddleware
from sambot.middlewares.i18n import MyI18nMiddleware
from sambot.utils.command_list import set_ui_commands
from sambot.utils.devices import DeviceScraper
from sambot.utils.logging import log
from sambot.utils.notify import sync_firmwares


async def main():
    if config.sentry_url:
        log.info("Starting sentry.io integraion...")

        sentry_sdk.init(
            str(config.sentry_url),
            traces_sample_rate=1.0,
        )

    await create_tables()

    dp.message.middleware(ACLMiddleware())
    dp.message.middleware(MyI18nMiddleware(i18n=i18n))
    dp.callback_query.middleware(ACLMiddleware())
    dp.callback_query.middleware(MyI18nMiddleware(i18n=i18n))

    dp.include_routers(
        pm_menu.router,
        doas.router,
        language.router,
        tools.router,
    )

    await set_ui_commands(bot, i18n)

    aiocron.crontab(
        "0 */6 * * *",
        func=sync_firmwares,
        loop=asyncio.get_event_loop(),
        tz=datetime.UTC,
    )
    aiocron.crontab(
        "0 0 1 * *",
        func=DeviceScraper.sync_devices,
        loop=asyncio.get_event_loop(),
        tz=datetime.UTC,
    )

    with suppress(TelegramForbiddenError):
        if config.logs_channel:
            log.info("Sending startup notification...")
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
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("Samsung Helper Bot stopped!")
