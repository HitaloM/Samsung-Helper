# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

import asyncio

import aiohttp


class FWClient:
    def __init__(self) -> None:
        self.fetch_interval: int = 3

    async def get_device_doc(self, model: str, redion: str):
        await asyncio.sleep(self.fetch_interval)
        async with aiohttp.ClientSession() as session:
            r = await session.get(url=f"https://doc.samsungmobile.com/{model}/{redion}/doc.html")
            return await r.content.read()

    async def get_device_eng(self, model: str, magic: str):
        await asyncio.sleep(self.fetch_interval)
        async with aiohttp.ClientSession() as session:
            r = await session.get(url=f"https://doc.samsungmobile.com/{model}/{magic}/eng.html")
            return await r.content.read()
