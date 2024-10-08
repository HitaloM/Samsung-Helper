# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio

import aiohttp

from sambot.utils.logging import log

from .headers import GENERIC_HEADER


class FWClient:
    def __init__(self) -> None:
        self.max_retries: int = 5
        self.retry_backoff: float = 2.0

    async def fetch_with_retry(self, url: str):
        retries = 0
        await asyncio.sleep(3)
        while retries < self.max_retries:
            try:
                async with (
                    aiohttp.ClientSession(
                        timeout=aiohttp.ClientTimeout(60), headers=GENERIC_HEADER
                    ) as session,
                    session.get(url) as response,
                ):
                    response.raise_for_status()
                    return await response.text()
            except (aiohttp.ClientConnectorError, aiohttp.ClientError):
                retries += 1
                await asyncio.sleep(self.retry_backoff**retries)
            except Exception as e:
                log.error("[FWClient] Unexpected error: %s", e)
                break

        log.error("[FWClient] Failed to fetch %s after %s retries", url, self.max_retries)
        return None

    async def get_device_doc(self, model: str, region: str):
        url = f"https://doc.samsungmobile.com/{model}/{region}/doc.html"
        return await self.fetch_with_retry(url)

    async def get_device_eng(self, model: str, magic: str):
        url = f"https://doc.samsungmobile.com/{model}/{magic}/eng.html"
        return await self.fetch_with_retry(url)
