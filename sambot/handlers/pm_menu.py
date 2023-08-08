# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

import html

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
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
    keyboard.button(text=_("ℹ️ About"), callback_data=StartCallback(menu="about"))
    keyboard.button(text=_("🌐 Language"), callback_data=StartCallback(menu="language"))
    keyboard.button(text=_("Samsung Firmwares Updater"), url="https://t.me/SamFirm")
    keyboard.adjust(2)

    text = _(
        "Hello <b>{user_name}</b>! I'm a bot made to help Samsung Galaxy users. \
You can have a look at my features in the help menu by clicking the button below.\n\n\
To checkout my commands just type in the <code>/</code> (bar) icon in the group and select \
a command or in the <i>menu</i> button in PM."
    ).format(user_name=html.escape(union.from_user.full_name))

    await (message.edit_text if is_callback else message.reply)(
        text,
        reply_markup=keyboard.as_markup(),
    )


@router.message(Command("about"))
@router.callback_query(StartCallback.filter(F.menu == "about"))
async def about(union: Message | CallbackQuery):
    is_callback = isinstance(union, CallbackQuery)
    message = union.message if is_callback else union
    if not message:
        return

    text = _("This bot is made to help Samsung Galaxy users.")

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=_("📦 GitHub"), url="https://github.com/HitaloM/Samsung-Helper")
    keyboard.button(text=_("📚 Channel"), url="https://t.me/HitaloProjects")
    keyboard.adjust(2)

    if is_callback or message.chat.type == ChatType.PRIVATE:
        keyboard.row(
            InlineKeyboardButton(
                text=_("🔙 Back"), callback_data=StartCallback(menu="start").pack()
            )
        )

    await (message.edit_text if is_callback else message.reply)(
        text,
        reply_markup=keyboard.as_markup(),
    )
