# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

import html

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder

from sambot.utils.callback_data import StartCallback

router = Router(name="pm_menu")


@router.message(CommandStart(), F.chat.type == ChatType.PRIVATE)
@router.callback_query(StartCallback.filter(F.menu == "start"))
async def start_command(union: Message | CallbackQuery):
    is_callback = isinstance(union, CallbackQuery)
    message = union.message if is_callback else union
    if not message or not union.from_user:
        return

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=_("🌐 Language"), callback_data=StartCallback(menu="language"))

    text = _(
        "Hello <b>{user_name}</b>! I'm a bot made to help Samsung Galaxy users. \
You can have a look at my features in the help menu by clicking the button below."
    ).format(user_name=html.escape(union.from_user.full_name))

    await (message.edit_text if is_callback else message.reply)(
        text,
        reply_markup=keyboard.as_markup(),
    )
