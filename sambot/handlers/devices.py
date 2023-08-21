# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

from aiogram import Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder

from sambot.database import devices_db
from sambot.utils.callback_data import DeviceCallback

router = Router(name="devices")


@router.message(Command("device"))
@router.callback_query(DeviceCallback.filter())
async def get_device(
    union: Message | CallbackQuery,
    command: CommandObject | None = None,
    callback_data: DeviceCallback | None = None,
):
    is_callback = isinstance(union, CallbackQuery)
    message = union.message if is_callback else union
    user = union.from_user
    if not message or not user:
        return

    is_private: bool = message.chat.type == ChatType.PRIVATE

    if command and not command.args:
        await message.reply(_("You need to specify an device. Use /device name"))
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

        is_search = callback_data.is_search
        if is_search and not is_private:
            await message.delete()

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
                        callback_data=DeviceCallback(
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

    device = await devices_db.get_device_by_id(int(qdevice))
    if not device:
        await message.reply(_("No device found."))
        return

    device_id = int(device[0])
    device_name = device[1]
    device_img = device[3]
    device_desc = device[4]

    text = f"<b>{device_name}</b>\n\n{device_desc}"

    await message.answer_photo(photo=device_img, caption=text)
