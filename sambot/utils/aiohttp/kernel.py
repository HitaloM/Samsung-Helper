# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

import asyncio

import aiohttp


class KernelClient:
    def __init__(self) -> None:
        self.fetch_interval: int = 3

    async def search(self, model: str):
        await asyncio.sleep(self.fetch_interval)
        async with aiohttp.ClientSession() as session:
            r = await session.get(
                url=f"https://opensource.samsung.com/uploadSearch?searchValue={model}"
            )
            return await r.content.read()
