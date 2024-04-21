# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hide_link

from sambot.database import devices_db
from sambot.utils.callback_data import SpecCallback

router = Router(name="specs")


@router.message(Command("specs"))
@router.callback_query(SpecCallback.filter())
async def get_specs(
    union: Message | CallbackQuery,
    command: CommandObject | None = None,
    callback_data: SpecCallback | None = None,
):
    is_callback = isinstance(union, CallbackQuery)
    message = union.message if is_callback else union
    user = union.from_user
    if not message or not user:
        return

    if command and not command.args:
        await message.reply(_("You need to specify an device. Use /specs name"))
        return

    query = str(
        callback_data.device
        if is_callback and callback_data is not None
        else command.args
        if command and command.args
        else None
    )

    if is_callback and callback_data is not None:
        user_id = callback_data.user_id
        if user_id is not None:
            user_id = int(user_id)

            if user_id != user.id:
                await union.answer(
                    _("This button is not for you."),
                    show_alert=True,
                    cache_time=60,
                )
                return

    if not bool(query):
        return

    keyboard = InlineKeyboardBuilder()
    if not query.isdecimal():
        devices = await devices_db.search_devices(query)
        if not devices:
            await message.reply(_("No device found."))
            return

        if len(devices) == 1:
            qdevice = devices[0][0]
        else:
            for device in devices:
                device_id = int(device[0])
                device_name = device[1]

                keyboard.row(
                    InlineKeyboardButton(
                        text=device_name,
                        callback_data=SpecCallback(
                            device=device_id, user_id=user.id, is_search=True
                        ).pack(),
                    )
                )

            await message.reply(
                _("Search Results For: {query}").format(query=query),
                reply_markup=keyboard.as_markup(),
            )
            return
    else:
        qdevice = int(query)

    device_specs = await devices_db.get_specs_by_id(int(qdevice))
    if not device_specs:
        await message.reply(_("No specs found."))
        return

    device = await devices_db.get_device_by_id(int(qdevice))
    if not device:
        await message.reply(_("No device found."))
        return

    categories = {}
    for spec in device_specs:
        category = spec[1]
        if category not in categories:
            categories[category] = []
        categories[category].append(spec)

    device_name = device[1]
    device_img = device[3]
    response = _("<b>Specs for {device}</b>\n\n").format(device=device_name)
    for category, specs in categories.items():
        response += f"<b>{category}</b>\n"
        for spec in specs:
            spec_name = f"<b>{spec["name"]}</b>: " if spec["name"] else None
            spec_value = spec["value"] or None
            if spec_name and spec_value:
                response += f"{spec_name}{spec_value}\n"
        response += "\n"

    response += hide_link(device_img)

    if callback_data and callback_data.is_search:
        await message.edit_text(response, disable_web_page_preview=False, reply_markup=None)
        return

    await message.reply(response, disable_web_page_preview=False)
