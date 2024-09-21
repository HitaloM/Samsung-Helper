# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio

import aiohttp
from aiohttp import ClientConnectorError

from sambot.utils.logging import log


class FWClient:
    def __init__(self) -> None:
        self.max_retries: int = 5
        self.retry_backoff: float = 1.5

    async def fetch_with_retry(self, url: str):
        retries = 0
        while retries < self.max_retries:
            try:
                async with aiohttp.ClientSession() as session, session.get(url) as response:
                    response.raise_for_status()
                    return await response.text()
            except (ClientConnectorError, aiohttp.ClientError):
                retries += 1
                await asyncio.sleep(self.retry_backoff**retries)
            except Exception as e:
                log.error("[FWClient] Unexpected error: %s", e)
                break

        log.error("[FWClient] Failed to fetch %s after %s retries", url, self.max_retries)
        return None

    async def get_device_doc(self, model: str, region: str):
        url = f"https://cors-bypass.amano.workers.dev/https://doc.samsungmobile.com/{model}/{region}/doc.html"
        return await self.fetch_with_retry(url)

    async def get_device_eng(self, model: str, magic: str):
        url = f"https://cors-bypass.amano.workers.dev/https://doc.samsungmobile.com/{model}/{magic}/eng.html"
        return await self.fetch_with_retry(url)
