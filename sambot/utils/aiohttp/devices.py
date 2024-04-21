# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

import asyncio

import aiohttp

HEADERS: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "referer": "https://www.gsmarena.com/",
}


class GSMClient:
    def __init__(self) -> None:
        self.fetch_interval: int = 3

    async def get_devices_list(self, page: int):
        await asyncio.sleep(self.fetch_interval)
        url = "https://cors-bypass.amano.workers.dev/https://www.gsmarena.com/samsung-phones-9.php"
        if page != 1:
            url = f"https://cors-bypass.amano.workers.dev/https://www.gsmarena.com/samsung-phones-f-9-0-p{page!s}.php"

        async with aiohttp.ClientSession() as session:
            r = await session.get(url, headers=HEADERS)
            return await r.content.read()

    async def get_device(self, url: str):
        await asyncio.sleep(self.fetch_interval)
        async with aiohttp.ClientSession() as session:
            r = await session.get(
                f"https://cors-bypass.amano.workers.dev/https://www.gsmarena.com/{url}",
                headers=HEADERS,
            )
            return await r.content.read()


class RegionsClient:
    def __init__(self) -> None:
        self.fetch_interval: int = 3

    async def get_regions(self, model: str):
        await asyncio.sleep(self.fetch_interval)
        async with aiohttp.ClientSession() as session:
            r = await session.get(url=f"https://www.samfw.com/firmware/{model}")
            return await r.content.read()
