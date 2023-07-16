# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

import asyncio

from .client import AiohttpBaseClient, HttpResponseObject


class KernelClient(AiohttpBaseClient):
    def __init__(self) -> None:
        self.base_url: str = "https://opensource.samsung.com/"
        self.fetch_interval: int = 3
        super().__init__(base_url=self.base_url)

    async def search(self, model: str) -> HttpResponseObject:
        await asyncio.sleep(self.fetch_interval)
        return await self._make_request(
            "GET",
            url=f"/uploadSearch?searchValue={model}",
            get_text=True,
        )

    async def download_by_id(self, upload_id: str) -> HttpResponseObject:
        await asyncio.sleep(self.fetch_interval)
        return await self._make_request(
            "GET",
            url=f"/downSrcMPop?uploadId={upload_id}",
            get_text=True,
            get_cookies=True,
        )
