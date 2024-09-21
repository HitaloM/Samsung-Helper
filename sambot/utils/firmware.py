# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from asyncio import CancelledError
from dataclasses import dataclass
from datetime import datetime

from bs4 import BeautifulSoup

from sambot.utils.aiohttp.firmware import FWClient
from sambot.utils.logging import log
from sambot.utils.pda import (
    get_build_id,
    get_build_month,
    get_build_year,
    get_major_version,
)


@dataclass(slots=True)
class FirmwareMeta:
    model: str
    region: str
    os_version: str
    pda: str
    build_date: datetime
    securitypatch: datetime
    name: str
    changelog: str

    def download_url(self) -> str:
        return f"https://samfw.com/firmware/{self.model}/{self.region}/{self.pda}"

    def is_newer_than(self, old_pda) -> bool:
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
        return self.__dict__

    def __str__(self) -> str:
        return str(self.raw())


async def fetch_latest_firmware(model: str, region: str) -> FirmwareMeta | None:
    try:
        device_doc = await FWClient().get_device_doc(model, region)
        if not device_doc:
            log.error(
                "[SamsungFirmwareInfo] Failed to fetch device document",
                model=model,
                region=region,
            )
            return None

        magic = extract_magic(device_doc)
        if not magic:
            return None

        device_eng = await FWClient().get_device_eng(model, magic)
        if not device_eng:
            log.error(
                "[SamsungFirmwareInfo] Failed to fetch device engineering document",
                model=model,
                magic=magic,
            )
            return None

        return parse_firmware_meta(device_eng, model, region)
    except (KeyboardInterrupt, CancelledError):
        raise
    except BaseException:
        log.exception("[SamsungFirmwareInfo] Failed to fetch latest firmware info")
        return None


def extract_magic(device_doc: str) -> str | None:
    soup = BeautifulSoup(device_doc, features="xml")
    inp = soup.find(id="dflt_page")
    if inp is not None:
        return inp["value"].split("/")[3]  # type: ignore
    return None


def parse_firmware_meta(device_eng: str, model: str, region: str) -> FirmwareMeta | None:
    soup = BeautifulSoup(device_eng, features="xml")
    changelog_entries = soup.find_all(class_="row")
    if len(changelog_entries) < 2:
        return None

    latest_entry = changelog_entries[1]
    info = latest_entry.find_all(class_="col-md-3")
    if len(info) < 4:
        return None

    pda = info[0].text.split(":")[1].strip()
    os_version = info[1].text.split(":")[1].strip().replace("(Android ", " (")
    release_date = info[2].text.split(":")[1].strip()
    security_patch = info[3].text.split(":")[1].strip()
    name = extract_name(soup)
    changelog_txt = extract_changelog(soup)

    return FirmwareMeta(
        model=model,
        region=region,
        os_version=os_version,
        pda=pda,
        build_date=datetime.strptime(release_date, "%Y-%m-%d"),  # noqa: DTZ007
        securitypatch=datetime.strptime(security_patch, "%Y-%m-%d"),  # noqa: DTZ007
        name=name,
        changelog=changelog_txt,
    )


def extract_name(soup: BeautifulSoup) -> str:
    h1 = soup.find_all("h1")
    if h1:
        return h1[0].text.split("(")[0].strip()
    return ""


def extract_changelog(soup: BeautifulSoup) -> str:
    for br in soup.find_all("br"):
        br.replace_with("\n")

    changelog_text = soup.find_all("span")
    if len(changelog_text) > 1:
        return changelog_text[1].get_text()
    return ""
