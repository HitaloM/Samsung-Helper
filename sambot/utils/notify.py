# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

import asyncio

from aiogram.exceptions import TelegramRetryAfter
from aiogram.utils.keyboard import InlineKeyboardBuilder

from sambot import bot
from sambot.config import config
from sambot.database import Firmwares, devices_db
from sambot.utils.firmware import FirmwareInfo
from sambot.utils.logging import log


async def sync_firmwares() -> None:
    if not config.fw_channel:
        log.error("[FirmwaresSync] - Firmware channel not set!")
        return

    firmwares_db = Firmwares()

    all_models = await devices_db.get_all_models()
    if not all_models:
        log.warn("[FirmwaresSync] - No models found in database!")
        return

    for model in all_models:
        log.info("[FirmwaresSync] - Checking model: %s", model)

        model_regions = await devices_db.get_regions_by_model(model)
        if not model_regions:
            log.warn("[FirmwaresSync] - No regions found for model: %s", model)
            continue

        for region in model_regions:
            info = await FirmwareInfo.fetch_latest(model, region)

            if info:
                log.info(
                    "[FirmwaresSync] - Found firmware %s/%s for model %s", region, info.pda, model
                )
                if not info:
                    log.warn(
                        "[FirmwaresSync] - Model %s not found in any known region! "
                        "Known Regions: %s",
                        model,
                        devices_db.get_regions_by_model(model),
                    )

                pda = await firmwares_db.get_pda(model)
                if pda and info.is_newer_than(str(pda)):
                    keyboard = InlineKeyboardBuilder()
                    keyboard.button(text="Channel", url="https://t.me/SamFirm")
                    keyboard.button(text="Group", url="https://t.me/SamFirm_chat")
                    keyboard.button(text="⬇️ Download", url=info.download_url())
                    keyboard.adjust(2)

                    build_date = info.build_date.strftime("%Y-%m-%d")
                    securitypatch = info.securitypatch.strftime("%Y-%m-%d")
                    text = (
                        "<b>New firmware update available!</b>\n\n"
                        f"<b>Device:</b> <code>{info.name}</code>\n"
                        f"<b>Model:</b> <code>{info.model}</code>\n"
                        f"<b>Android Version:</b> <code>{info.os_version}</code>\n"
                        f"<b>Build Number:</b> <code>{info.pda}</code>\n"
                        f"<b>Release Date:</b> <code>{build_date}</code>\n"
                        f"<b>Security Patch Level:</b> <code>{securitypatch}</code>\n\n"
                        f"<b>Changelog:</b>\n{info.changelog}"
                    )

                    await asyncio.sleep(0.5)
                    try:
                        await bot.send_message(
                            chat_id=config.fw_channel, text=text, reply_markup=keyboard.as_markup()
                        )
                    except TelegramRetryAfter as e:
                        log.warn(
                            "[FirmwaresSync] - Telegram Retry-After: %s seconds", e.retry_after
                        )
                        await asyncio.sleep(e.retry_after)
                        await bot.send_message(
                            chat_id=config.fw_channel, text=text, reply_markup=keyboard.as_markup()
                        )

                    await firmwares_db.set_pda(model, info.pda)
