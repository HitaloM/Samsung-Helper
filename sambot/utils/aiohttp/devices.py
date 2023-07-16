# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

import asyncio

from .client import AiohttpBaseClient, HttpResponseObject


class GSMClient(AiohttpBaseClient):
    def __init__(self) -> None:
        self.base_url: str = "https://www.gsmarena.com"
        self.fetch_interval: int = 3
        super().__init__(base_url=self.base_url)

    async def get_devices_list(self, page: int) -> HttpResponseObject:
        await asyncio.sleep(self.fetch_interval)
        return await self._make_request(
            "GET",
            url=f"/samsung-phones-f-9-0-p{str(page)}.php",
            get_text=True,
        )

    async def get_device(self, url: str) -> HttpResponseObject:
        await asyncio.sleep(self.fetch_interval)
        return await self._make_request(
            "GET",
            url=f"/{url}",
            get_text=True,
        )


class RegionsClient(AiohttpBaseClient):
    def __init__(self) -> None:
        self.base_url: str = "https://www.samfw.com"
        self.fetch_interval: int = 3
        super().__init__(base_url=self.base_url)

    async def get_regions(self, model: str) -> HttpResponseObject:
        await asyncio.sleep(self.fetch_interval)
        return await self._make_request(
            "GET",
            url=f"/firmware/{model}",
            get_text=True,
        )
