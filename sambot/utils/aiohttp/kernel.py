# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio

import aiohttp

from .headers import GENERIC_HEADER


class KernelClient:
    def __init__(self) -> None:
        self.fetch_interval: int = 3

    async def search(self, model: str):
        await asyncio.sleep(self.fetch_interval)
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(60), headers=GENERIC_HEADER
        ) as session:
            r = await session.get(
                url=f"https://opensource.samsung.com/uploadSearch?searchValue={model}"
            )
            return await r.content.read()
