# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

import asyncio
from datetime import datetime

from aiogram.exceptions import TelegramRetryAfter
from aiogram.utils.keyboard import InlineKeyboardBuilder

from sambot import bot
from sambot.config import config
from sambot.database import Firmwares, devices_db
from sambot.utils.channel_logging import channel_log
from sambot.utils.firmware import FirmwareInfo
from sambot.utils.logging import log

fw_queue = asyncio.Queue()


async def process_firmware(model: str):
    if not config.fw_channel:
        log.error("[FirmwaresSync] - Firmware channel not set!")
        return

    firmwares_db = Firmwares()

    model_regions = await devices_db.get_regions_by_model(model)
    if not model_regions:
        log.warn("[FirmwaresSync] - No regions found for model: %s", model)
        return

    if model_regions:
        for region in model_regions:
            info = await FirmwareInfo.fetch_latest(model, region)

            if not info:
                log.warn(
                    "[FirmwaresSync] - Model %s not found in any known region! "
                    "Known Regions: %s",
                    model,
                    await devices_db.get_regions_by_model(model),
                )
            else:
                log.info(
                    "[FirmwaresSync] - Found firmware %s/%s for model %s",
                    region,
                    info.pda,
                    model,
                )

                pda = await firmwares_db.get_pda(model)

                if pda and info.is_newer_than(str(pda)):
                    keyboard = InlineKeyboardBuilder()
                    keyboard.button(text="Download ⬇️", url=info.download_url())

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
                            chat_id=config.fw_channel,
                            text=text,
                            reply_markup=keyboard.as_markup(),
                        )
                    except TelegramRetryAfter as e:
                        log.warn(
                            "[FirmwaresSync] - Telegram Retry-After: %s seconds", e.retry_after
                        )
                        await asyncio.sleep(e.retry_after)
                        await bot.send_message(
                            chat_id=config.fw_channel,
                            text=text,
                            reply_markup=keyboard.as_markup(),
                        )
                    finally:
                        await channel_log(
                            text=(
                                "<b>New firmware detected for"
                                f"{info.name}</b> (<code>{info.model}</code>)"
                            )
                        )

                    await firmwares_db.set_pda(model, info.pda)


async def sync_firmwares():
    log.info("[FirmwaresSync] - Starting firmware sync...")
    if not fw_queue.empty():
        log.warn("[FirmwaresSync] - Queue is not empty, aborting sync!")
        await channel_log(
            text="<b>Alert!</b> Firmware sync aborted because the queue is not empty!"
        )
        return

    await channel_log(
        text=(
            "<b>Starting firmwares sync...</b>\n\n"
            f"<b>Time</b>: <code>{datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}</code>\n"
        )
    )

    all_models = await devices_db.get_all_models()
    if not all_models:
        log.warn("[FirmwaresSync] - No models found in database!")
        return

    for model in all_models:
        log.debug("[FirmwaresSync] - Adding model to the queue: %s", model)
        await fw_queue.put(model)

    async def task():
        while True:
            try:
                model = await asyncio.wait_for(fw_queue.get(), timeout=60)
            except asyncio.TimeoutError:
                break
            else:
                log.info("[FirmwaresSync] - Checking model: %s", model)
                await process_firmware(model)

    tasks = [asyncio.create_task(task()) for _ in range(5)]

    await asyncio.gather(*tasks)

    await channel_log(
        text=(
            "<b>Firmwares sync finished!</b>\n\n"
            f"<b>Time</b>: <code>{datetime.now().strftime('%d/%m/%Y - %H:%M:%S')}</code>\n"
        )
    )
