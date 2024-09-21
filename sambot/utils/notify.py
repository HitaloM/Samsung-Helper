# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
from datetime import UTC, datetime

from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.utils.keyboard import InlineKeyboardBuilder

from sambot import bot
from sambot.config import config
from sambot.database import Devices, Firmwares
from sambot.utils.channel_logging import channel_log
from sambot.utils.firmware import FirmwareMeta, fetch_latest_firmware
from sambot.utils.logging import log

fw_queue = asyncio.Queue()


async def process_firmware(model: str):
    if not config.fw_channel:
        log.warn("[FirmwaresSync] - Firmware channel not set!")
        return

    firmwares_db = Firmwares()

    model_regions = await Devices().get_regions_by_model(model)
    if not model_regions:
        log.warn("[FirmwaresSync] - No regions found for model %s!", model)
        return

    await process_regions(model, model_regions, firmwares_db)


async def process_regions(model: str, model_regions: list | str, firmwares_db: Firmwares):
    for region in model_regions:
        info = await fetch_latest_firmware(model, region)

        if not info:
            log.warn(
                "[FirmwaresSync] - No firmware found for model %s in region %s!",
                model,
                region,
            )
        else:
            log.info(
                "[FirmwaresSync] - Found firmware for model %s in region %s: PDA %s",
                model,
                region,
                info.pda,
            )

            pda = await firmwares_db.get_pda(model)
            if pda and info.is_newer_than(str(pda)):
                await notify_new_firmware(info, model, firmwares_db)


async def notify_new_firmware(info: FirmwareMeta, model: str, firmwares_db: Firmwares):
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
            chat_id=config.fw_channel,  # type: ignore
            text=text,
            reply_markup=keyboard.as_markup(),
        )
    except TelegramRetryAfter as e:
        log.warn(
            "[FirmwaresSync] - Rate limited! Waiting %s seconds to retry...",
            e.retry_after,
        )
        await asyncio.sleep(e.retry_after)
        await bot.send_message(
            chat_id=config.fw_channel,  # type: ignore
            text=text,
            reply_markup=keyboard.as_markup(),
        )
    except TelegramBadRequest as e:
        if "message is too long" in str(e):
            await bot.send_message(
                chat_id=config.fw_channel,  # type: ignore
                text=text[:4090] + "[...]",
                reply_markup=keyboard.as_markup(),
            )
        else:
            log.exception("[FirmwaresSync] - Telegram Bad Request error: %s", e.message)
            await channel_log(
                text=(
                    "<b>Alert!</b> Firmware sync encountered an error!\n"
                    f"<b>Error:</b> <code>{e.message}</code>"
                )
            )
    finally:
        try:
            await channel_log(
                text=(f"<b>New firmware detected for {info.name}</b> (<code>{info.model}</code>)")
            )
        except TelegramRetryAfter as e:
            log.warn(
                "[FirmwaresSync] - Rate limited! Waiting %s seconds to retry...",
                e.retry_after,
            )
            await asyncio.sleep(e.retry_after)

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
            f"<b>Time</b>: <code>{datetime.now(tz=UTC).strftime("%d/%m/%Y, %H:%M:%S")}</code>\n"
        )
    )

    all_models = await Devices().get_all_models()
    if not all_models:
        log.warn("[FirmwaresSync] - No models found in database!")
        return

    for model in all_models:
        log.debug("[FirmwaresSync] - Adding model %s to the queue.", model)
        await fw_queue.put(model)

    async def task():
        while not fw_queue.empty():
            try:
                model = await asyncio.wait_for(fw_queue.get(), timeout=60)
            except TimeoutError:
                break
            else:
                log.info("[FirmwaresSync] - Processing model %s.", model)
                await process_firmware(model)

    async with asyncio.TaskGroup() as tg:
        for _ in range(10):
            tg.create_task(task())

    await channel_log(
        text=(
            "<b>Firmwares sync finished!</b>\n\n"
            f"<b>Time</b>: <code>{datetime.now(tz=UTC).strftime("%d/%m/%Y - %H:%M:%S")}</code>\n"
        )
    )
