# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import re
from asyncio import CancelledError
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlencode

import aiohttp
from aiofile import async_open
from bs4 import BeautifulSoup
from yarl import URL

from sambot import app_dir
from sambot.config import Settings
from sambot.utils.aiohttp.kernel import KernelClient
from sambot.utils.logging import log
from sambot.utils.pda import (
    get_build_id,
    get_build_month,
    get_build_year,
    get_major_version,
)

OSS_BASE_URL = "https://opensource.samsung.com"
OSS_SEARCH_URL = f"{OSS_BASE_URL}/uploadSearch?searchValue="


@dataclass(slots=True)
class KernelMeta:
    model: str = ""
    pda: str = ""
    upload_id: str = ""
    patch_kernel: str | None = None

    def is_newer_than(self, old_pda: str) -> bool:
        if len(old_pda) < 4:
            return True

        if len(self.pda) < 4:
            return False

        if get_major_version(self.pda) > get_major_version(old_pda):
            return True

        if get_major_version(self.pda) == get_major_version(old_pda):
            if get_build_year(self.pda) > get_build_year(old_pda):
                return True

            if get_build_year(self.pda) == get_build_year(old_pda):
                if get_build_month(self.pda) > get_build_month(old_pda):
                    return True

                if get_build_month(self.pda) == get_build_month(old_pda):
                    return get_build_id(self.pda) > get_build_id(old_pda)

        return False

    def raw(self) -> dict:
        return asdict(self)

    def __str__(self) -> str:
        return str(self.raw())

    async def download(self, folder: Path = app_dir / "data/downloads/") -> Path | None:
        dst = folder / f"{self.model}-{self.pda}.zip"
        async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
            response = await session.get(
                f"{OSS_BASE_URL}/downSrcMPop?uploadId={self.upload_id}", allow_redirects=False
            )
            data = await response.content.read()

        doc = BeautifulSoup(data, "lxml")
        _csrf_elem = doc.find_all(attrs={"name": "_csrf"})
        checkboxes = doc.find_all(attrs={"type": "checkbox"})

        attach_ids = self._extract_attach_ids(doc, checkboxes)
        if not attach_ids:
            log.error("[SamsungKernelInfo] - Did not find attachment!", kernel=self.raw())
            return None

        query, cookies_str = self._prepare_download_query(doc, _csrf_elem, attach_ids, session)
        if not query:
            return None

        return await self._download_file(dst, query, cookies_str)

    def _extract_attach_ids(self, doc: BeautifulSoup, checkboxes: list) -> str | None:
        if len(checkboxes) <= 1:
            return None
        if self.patch_kernel is None:
            return checkboxes[1]["id"]

        for row in doc.find_all("tr"):
            row_data = row.find_all("td")
            if len(row_data) >= 2 and row_data[1].get_text().endswith(f"{self.pda}.zip"):
                return ",".join(
                    checkbox["id"]
                    for checkbox in row.find_all(attrs={"type": "checkbox"})
                    if checkbox["id"].isdigit()
                )
        return None

    def _prepare_download_query(
        self, doc: BeautifulSoup, _csrf_elem: list, attach_ids: str, session: aiohttp.ClientSession
    ) -> tuple[bytes | None, str | None]:
        token_elem = doc.find(id="token")
        if token_elem is None:
            return None, None

        token = token_elem.get("value")  # type: ignore
        _csrf = _csrf_elem[0]["value"]
        query = (
            f"_csrf={_csrf}&uploadId={self.upload_id}&attachIds={attach_ids}"
            f"&downloadPurpose=ETC&{urlencode({"token": token})}"
        ).encode()

        cookies_str = (
            "; ".join(
                f"{key}={cookie.value}"
                for key, cookie in session.cookie_jar.filter_cookies(URL(OSS_BASE_URL)).items()
            )
            + "; __COM_SPEED=H; device_type=pc; fileDownload=true"
        )

        return query, cookies_str

    async def _download_file(
        self, dst: Path, query_bin: bytes, cookies_str: str | None
    ) -> Path | None:
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Content-Length": str(len(query_bin)),
            "Cookie": cookies_str,
            "Origin": OSS_BASE_URL,
            "Referer": f"{OSS_SEARCH_URL}{self.model}",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0",
        }

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5400)) as session:
            config = Settings()  # type: ignore
            response = await session.post(
                f"{config.cors_bypass}/https://opensource.samsung.com/downSrcCode",
                headers=headers,
                data=query_bin,
            )
            if (
                response.status == 200
                and response.headers.get("Content-Transfer-Encoding") == "binary"
            ):
                async with async_open(dst, "wb") as file:
                    async for chunk in response.content.iter_chunked(16144):
                        await file.write(chunk)
                return dst

        return None


async def fetch_latest_kernel(model: str) -> KernelMeta | None:
    try:
        kernel_search = await KernelClient().search(model)
        soup = BeautifulSoup(kernel_search, "lxml")
        table_rows = soup.find_all("tr")

        for table_row in table_rows:
            table_data = table_row.find_all("td")

            if len(table_data) > 4:
                models = table_data[1].get_text(strip=True).split("<br>")

                if model in models:
                    fw_versions = table_data[2].get_text(strip=True).split("<br>")
                    fw_version = re.sub(
                        "[^a-zA-Z0-9]", "", fw_versions[-1].strip() if fw_versions else ""
                    )

                    upload_id = ""
                    download_td = table_data[4].find("a").get("href").split("'")

                    if len(download_td) > 1:
                        upload_id = download_td[1].strip()

                    download_files = table_data[3].get_text(strip=True, separator=" ").split(" ")
                    if len(download_files) > 1:
                        patch_version = download_files[-1].split("_")[-1].split(".")[0]

                        return KernelMeta(
                            model=model,
                            pda=patch_version,
                            upload_id=upload_id,
                            patch_kernel=fw_version,
                        )

                    return KernelMeta(
                        model=model,
                        pda=fw_version,
                        upload_id=upload_id,
                        patch_kernel=None,
                    )
    except (KeyboardInterrupt, CancelledError):
        raise
    except Exception as e:
        log.error(f"[SamsungKernelInfo] - Failed to fetch latest kernel! Error: {e}", device=model)
        return None
