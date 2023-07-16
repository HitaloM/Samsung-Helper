# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

import asyncio

from .client import AiohttpBaseClient, HttpResponseObject


class FWClient(AiohttpBaseClient):
    def __init__(self) -> None:
        self.base_url: str = "https://doc.samsungmobile.com/"
        self.fetch_interval: int = 3
        super().__init__(base_url=self.base_url)

    async def get_device_doc(self, model: str, redion: str) -> HttpResponseObject:
        await asyncio.sleep(self.fetch_interval)
        return await self._make_request(
            "GET",
            url=f"/{model}/{redion}/doc.html",
            get_text=True,
        )

    async def get_device_eng(self, model: str, magic: str) -> HttpResponseObject:
        await asyncio.sleep(self.fetch_interval)
        return await self._make_request(
            "GET",
            url=f"/{model}/{magic}/eng.html",
            get_text=True,
        )
