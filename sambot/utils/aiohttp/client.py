# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

import asyncio
import logging
import ssl
from collections.abc import Callable
from http.cookies import SimpleCookie
from typing import Any

import backoff
import msgspec
from aiohttp import ClientError, ClientSession, TCPConnector
from multidict import CIMultiDictProxy
from yarl import URL

_JsonLoads = Callable[..., Any]
_JsonDumps = Callable[..., str]


class HttpResponseObject:
    def __init__(
        self,
        status: int,
        data: Any,
        headers: CIMultiDictProxy[str],
        binary: bytes | None = None,
        cookies: SimpleCookie[str] | None = None,
    ) -> None:
        self.status = status
        self.data = data
        self.headers = headers
        self.binary = binary
        self.cookies = cookies


class AiohttpBaseClient:
    def __init__(self, base_url: str | URL) -> None:
        self._base_url = base_url
        self._session: ClientSession | None = None
        self.json_loads: _JsonLoads = msgspec.json.decode
        self.json_dumps: _JsonDumps = lambda obj, *, enc_hook=None: msgspec.json.encode(
            obj, enc_hook=enc_hook
        ).decode()
        self.log = logging.getLogger(self.__class__.__name__)

    async def _get_session(self) -> ClientSession:
        if self._session is None:
            ssl_context = ssl.SSLContext()
            connector = TCPConnector(ssl_context=ssl_context)
            self._session = ClientSession(
                base_url=self._base_url,
                connector=connector,
                json_serialize=self.json_dumps,
            )

        return self._session

    @backoff.on_exception(backoff.expo, ClientError, max_tries=2)
    async def _make_request(
        self,
        method: str,
        url: str | URL,
        params: dict | None = None,
        json: dict | None = None,
        headers: dict | None = None,
        data: dict | None = None,
        get_text: bool = False,
        geat_binary: bool = False,
        get_cookies: bool = False,
    ) -> HttpResponseObject:
        session = await self._get_session()

        self.log.debug(
            "Making request %r %r with json %r and params %r",
            method,
            url,
            json,
            params,
        )
        async with session.request(
            method,
            url,
            params=params,
            json=json,
            headers=headers,
            data=data,
        ) as response:
            status = response.status
            if get_text:
                result = await response.text()
            else:
                result = await response.json(loads=self.json_loads)

            if geat_binary:
                binary = await response.read()
            else:
                binary = None

            cookies = response.cookies if get_cookies else None

        self.log.debug(
            "Got response %r %r with status %r and json %r",
            method,
            url,
            status,
            result,
        )
        return HttpResponseObject(
            status,
            result,
            response.headers,
            binary=binary,
            cookies=cookies,
        )

    async def close(self) -> None:
        if not self._session:
            self.log.debug("There's not session to close.")
            return

        if self._session.closed:
            self.log.debug("Session already closed.")
            return

        await self._session.close()
        self.log.debug("Session successfully closed.")

        # Wait 250 ms for the underlying SSL connections to close
        # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
        await asyncio.sleep(0.250)
