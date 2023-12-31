# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

from aiogram.enums import ChatType
from aiogram.types import CallbackQuery, Message

from sambot.database import chats_db, users_db


async def get_chat_language(
    union: Message | CallbackQuery,
) -> tuple[str | None, list | str | None]:
    is_callback = isinstance(union, CallbackQuery)
    message = union.message if is_callback else union
    if not message or not union.from_user:
        return None, None

    if not message or not message.from_user:
        return message.chat.type, None

    language_code = None

    if message.chat.type == ChatType.PRIVATE:
        user = union.from_user
        language_code = await users_db.get_language(user=user)

    if message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        chat = message.chat
        language_code = await chats_db.get_language(chat=chat)

    return message.chat.type, language_code
