# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

import asyncio
from typing import Any

from aiohttp import ClientTimeout

from .client import AiohttpBaseClient


class GSMClient(AiohttpBaseClient):
    def __init__(self) -> None:
        self.base_url: str = "https://www.gsmarena.com"
        self.fetch_interval: int = 3
        self.timeout = ClientTimeout(total=60)
        super().__init__(base_url=self.base_url)

    async def get_devices_list(self, page: int) -> tuple[int, str | Any]:
        await asyncio.sleep(self.fetch_interval)
        return await self._make_request(
            "GET",
            url=f"/samsung-phones-f-9-0-p{str(page)}.php",
            get_text=True,
            timeout=self.timeout,
        )

    async def get_device(self, url: str) -> tuple[int, str | Any]:
        await asyncio.sleep(self.fetch_interval)
        return await self._make_request(
            "GET",
            url=f"/{url}",
            get_text=True,
            timeout=self.timeout,
        )


class RegionsClient(AiohttpBaseClient):
    def __init__(self) -> None:
        self.base_url: str = "https://www.samfw.com"
        self.fetch_interval: int = 3
        self.timeout = ClientTimeout(total=60)
        super().__init__(base_url=self.base_url)

    async def get_regions(self, model: str) -> tuple[int, str | Any]:
        await asyncio.sleep(self.fetch_interval)
        return await self._make_request(
            "GET",
            url=f"/firmware/{model}",
            get_text=True,
            timeout=self.timeout,
        )
