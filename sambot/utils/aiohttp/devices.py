# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio

import aiohttp

from .headers import GENERIC_HEADER

HEADERS = {**GENERIC_HEADER, "referer": "https://www.gsmarena.com/"}


class GSMClient:
    @staticmethod
    async def get_devices_list(page: int):
        url = "https://cors-bypass.amano.workers.dev/https://www.gsmarena.com/samsung-phones-9.php"
        if page != 1:
            url = f"https://cors-bypass.amano.workers.dev/https://www.gsmarena.com/samsung-phones-f-9-0-p{page!s}.php"

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60), headers=HEADERS
        ) as session:
            r = await session.get(url)
            return await r.content.read()

    @staticmethod
    async def get_device(url: str):
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            r = await session.get(
                f"https://cors-bypass.amano.workers.dev/https://www.gsmarena.com/{url}"
            )
            return await r.content.read()


class RegionsClient:
    @staticmethod
    async def get_regions(model: str):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=60), headers=GENERIC_HEADER
                ) as session:
                    r = await session.get(url=f"https://samfw.com/firmware/{model}")
                    return await r.content.read()
            except aiohttp.ClientError:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1)
        return None
