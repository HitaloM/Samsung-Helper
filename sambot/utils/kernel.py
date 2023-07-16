# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

import re
from pathlib import Path
from urllib.parse import urlencode

import aiofiles
import aiohttp
from bs4 import BeautifulSoup
from yarl import URL

from sambot import KernelSession, app_dir
from sambot.utils.logging import log

OSS_BASE_URL: str = "https://opensource.samsung.com"
OSS_SEARCH_URL: str = OSS_BASE_URL + "/uploadSearch?searchValue="


class SamsungKernelInfo:
    class KernelMeta:
        """
        Represents metadata for a Samsung kernel.

        Args:
            model (str): The model of the Samsung device.
            pda (str): The PDA version of the kernel.
            upload_id (str): The upload ID of the kernel.
            patch_kernel (str | None, optional): The patch kernel version of the kernel.
            Defaults to None.
        """

        def __init__(
            self,
            model: str = "",
            pda: str = "",
            upload_id: str = "",
            patch_kernel: str | None = None,
        ):
            self.model = model
            self.pda = pda
            self.upload_id = upload_id
            self.patch_kernel = patch_kernel

        @staticmethod
        def get_major_version(pda: str) -> int:
            """
            Returns the major version number of the given PDA version.

            Args:
                pda (str): The PDA version to extract the major version number from.

            Returns:
                int: The major version number of the given PDA version.
            """
            return int(pda[-4])

        @staticmethod
        def get_build_date1(pda: str) -> int:
            """
            Returns the build date 1 of the given PDA version.

            Args:
                pda (str): The PDA version to extract the build date 1 from.

            Returns:
                int: The build date 1 of the given PDA version.
            """
            return int(pda[-3])

        @staticmethod
        def get_build_date2(pda: str) -> int:
            """
            Returns the build date 2 of the given PDA version.

            Args:
                pda (str): The PDA version to extract the build date 2 from.

            Returns:
                int: The build date 2 of the given PDA version.
            """
            return int(pda[-2])

        @staticmethod
        def get_minor_version(pda: str) -> int:
            """
            Returns the minor version number of the given PDA version.

            Args:
                pda (str): The PDA version to extract the minor version number from.

            Returns:
                int: The minor version number of the given PDA version.
            """
            return int(pda[-1])

        def is_newer_than(self, old_pda: str) -> bool:
            """
            Determines whether the current kernel is newer than the given PDA version.

            Args:
                old_pda (str): The PDA version to compare against.

            Returns:
                bool: True if the current kernel is newer, False otherwise.
            """
            if len(old_pda) < 4:
                return True

            if len(self.pda) < 4:
                return False

            if self.get_major_version(self.pda) > self.get_major_version(old_pda):
                return True

            if self.get_major_version(self.pda) == self.get_major_version(old_pda):
                if self.get_build_date1(self.pda) > self.get_build_date1(old_pda):
                    return True

                if self.get_build_date1(self.pda) == self.get_build_date1(old_pda):
                    if self.get_build_date2(self.pda) > self.get_build_date2(old_pda):
                        return True

                    if self.get_build_date2(self.pda) == self.get_build_date2(old_pda):
                        return self.get_minor_version(self.pda) > self.get_minor_version(old_pda)

            return False

        def raw(self) -> dict:
            """
            Returns the raw dictionary representation of the DeviceMeta object.

            Returns:
                dict: A dictionary containing the raw data of the DeviceMeta object.
            """
            return self.__dict__

        def __str__(self) -> str:
            return str(self.raw())

        async def download(self, folder: Path = app_dir / "/data/downloads/") -> Path | None:
            """
            Downloads the kernel source code archive for the device represented by this DeviceMeta
            object.

            Args:
                folder (Path, optional): The folder to download the archive to. Defaults to app_dir

            Returns:
                Path | None: The path to the downloaded archive file, or None if the download
                failed.
            """
            dst = Path(folder) / f"{self.model}-{self.pda}.zip"
            async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
                r = await session.get(
                    f"{OSS_BASE_URL}/downSrcMPop?uploadId={self.upload_id}",
                    allow_redirects=False,
                )
                data = await r.text()

            doc = BeautifulSoup(data, "lxml")
            _csrf_elem = doc.find_all(attrs={"name": "_csrf"})
            checkboxes = doc.find_all(attrs={"type": "checkbox"})

            if len(_csrf_elem) > 0 and len(checkboxes) > 1:
                _csrf = _csrf_elem[0]["value"]
                attach_ids = None

                if self.patch_kernel is None:
                    attach_ids = checkboxes[1]["id"]
                else:
                    rows = doc.find_all("tr")

                    for row in rows:
                        rowData = row.find_all("td")

                        if len(rowData) >= 2:
                            download_file = rowData[1].get_text()
                            if download_file.endswith(f"{self.pda}.zip"):
                                checkboxes = row.find_all(attrs={"type": "checkbox"})

                            if len(checkboxes) > 0:
                                attach_ids = checkboxes[0]["id"]
                                break

                if attach_ids is None or attach_ids == "":
                    log.error("[SamsungKernelInfo] - Did not find attachment for %s", str(self))
                    return None

                token_elem = doc.find(id="token")
                if token_elem is not None:
                    token = token_elem.get("value")  # type: ignore
                    query = (
                        f"_csrf={_csrf}&uploadId={self.upload_id}&attachIds={attach_ids}"
                        f"&downloadPurpose=ETC&{urlencode({'token': token})}"
                    )
                    query_bin = query.encode()

                    cookies_str = ""
                    cookies = session.cookie_jar.filter_cookies(URL(f"{OSS_BASE_URL}"))
                    for key, cookie in cookies.items():
                        cookies_str += f"{key}={cookie.value}; "

                    cookies_str += "__COM_SPEED=H"
                    cookies_str += "; device_type=pc"
                    cookies_str += "; fileDownload=true"

                    cookies_dict = {
                        item.split("=")[0].strip(): item.split("=")[1].strip()
                        for item in cookies_str.split(";")
                        if item
                    }

                    headers = {
                        "Accept": "text/html,application/xhtml+xml,"
                        "application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                        "Content-Length": str(len(query_bin)),
                        "Cookie": cookies_str,
                        "Origin": OSS_BASE_URL,
                        "Referer": f"{OSS_SEARCH_URL}{self.model}",
                        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:90.0) "
                        "Gecko/20100101 Firefox/90.0",
                    }

                    timeout = aiohttp.ClientTimeout(total=3600)
                    async with aiohttp.ClientSession(
                        cookies=cookies_dict, timeout=timeout
                    ) as session:
                        r = await session.post(
                            "https://opensource.samsung.com/downSrcCode",
                            headers=headers,
                            data=query_bin,
                        )
                        if (
                            r.status == 200
                            and r.headers.get("Content-Transfer-Encoding") == "binary"
                        ):
                            async with aiofiles.open(dst, "wb") as f:
                                while True:
                                    chunk = await r.content.read(1024)
                                    if not chunk:
                                        break
                                    await f.write(chunk)

                        return dst

            return None

    async def fetch_latest(self, model: str) -> KernelMeta | None:
        """
        Fetches the latest kernel for the given Samsung device model.

        Args:
            model (str): The model of the Samsung device.

        Returns:
            KernelMeta | None: The metadata for the latest kernel, or None if the fetch failed.
        """
        try:
            r = await KernelSession.search(model)
            soup = BeautifulSoup(r.data, "lxml")
            table_rows = soup.find_all("tr")

            for table_row in table_rows:
                table_data = table_row.find_all("td")

                if len(table_data) > 4:
                    models = table_data[1].get_text(strip=True).split("<br>")

                    if model in models:
                        fw_versions = table_data[2].get_text(strip=True).split("<br>")
                        fw_version = fw_versions[-1].strip() if len(fw_versions) > 0 else ""
                        fw_version = re.sub("[^a-zA-Z0-9]", "", fw_version)

                        upload_id = ""
                        download_td = table_data[4].find("a").get("href").split("'")

                        if len(download_td) > 1:
                            upload_id = download_td[1].strip()

                        download_files = (
                            table_data[3].get_text(strip=True, separator=" ").split(" ")
                        )
                        if len(download_files) > 1:
                            broken = download_files[-1].split("_")
                            patch_version = broken[-1].split(".")[0]

                            return self.KernelMeta(
                                model=model,
                                pda=patch_version,
                                upload_id=upload_id,
                                patch_kernel=fw_version,
                            )

                        return self.KernelMeta(
                            model=model, pda=fw_version, upload_id=upload_id, patch_kernel=None
                        )
        except BaseException:
            log.error("[SamsungKernelInfo] - Failed to fetch latest kernel for model %s", model)
            return None
