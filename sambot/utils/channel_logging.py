# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

from sambot import bot, config


async def channel_log(text: str, **kwargs):
    if config.logs_channel:
        await bot.send_message(chat_id=config.logs_channel, text=text, **kwargs)
