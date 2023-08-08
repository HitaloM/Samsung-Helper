# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router(name="tools")

USB_DRIVER: str = "https://samfw.com/Odin/SAMSUNG_USB_Driver_for_Mobile_Phones.zip"
ODIN: str = "https://samfw.com/Odin/Samfw.com_Odin3_v3.14.4.zip"


@router.message(Command(commands=["tools", "odin"]))
async def samsung_tools(message: Message):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Odin v3.14.4", url=ODIN)
    keyboard.button(text="Samsung USB Drivers", url=USB_DRIVER)
    keyboard.adjust(2)

    text = _("<b>Below are some useful tools for Samsung Galaxy devices</b>:")
    await message.answer(text, reply_markup=keyboard.as_markup())
