# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

from contextlib import suppress

from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
)
from aiogram.utils.i18n import I18n


async def set_ui_commands(bot: Bot, i18n: I18n):
    _ = i18n.gettext

    with suppress(TelegramRetryAfter):
        await bot.delete_my_commands()
        for lang in i18n.available_locales:
            all_chats_commands: list[BotCommand] = [
                BotCommand(
                    command="device",
                    description=_("Get brief information about a device.", locale=lang),
                ),
                BotCommand(
                    command="specs",
                    description=_("Get specifications of a device.", locale=lang),
                ),
                BotCommand(
                    command="tools",
                    description=_("Get latest tools for Samsung Galaxy", locale=lang),
                ),
                BotCommand(
                    command="language",
                    description=_("Change bot language.", locale=lang),
                ),
                BotCommand(
                    command="about",
                    description=_("About the bot.", locale=lang),
                ),
            ]

            user_commands: list[BotCommand] = [
                BotCommand(command="start", description=_("Start the bot.", locale=lang)),
                BotCommand(command="help", description=_("Get bot help menu.", locale=lang)),
                *all_chats_commands,
            ]

            group_commands: list[BotCommand] = [
                *all_chats_commands
            ]  # temporary until I add more commands

            await bot.set_my_commands(
                commands=user_commands,
                scope=BotCommandScopeAllPrivateChats(),
                language_code=lang.split("_")[0].lower() if "_" in lang else lang,
            )

            await bot.set_my_commands(
                commands=group_commands,
                scope=BotCommandScopeAllGroupChats(),
                language_code=lang.split("_")[0].lower() if "_" in lang else lang,
            )
