# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

from datetime import date, datetime

from bs4 import BeautifulSoup

from sambot import FWSession
from sambot.utils.logging import log

DATE_FORMAT: str = "%Y-%m-%d"


class SamsungFirmwareInfo:
    """
    Class that provides methods to fetch firmware information from the Samsung Firmware website.
    """

    class FirmwareMeta:
        def __init__(
            self,
            model: str,
            region: str,
            os_version: str,
            pda: str,
            build_date: date,
            securitypatch: date,
            name: str,
            changelog: str,
        ) -> None:
            self.model = model
            self.region = region
            self.os_version = os_version
            self.pda = pda
            self.build_date = build_date
            self.securitypatch = securitypatch
            self.name = name
            self.changelog = changelog

        def download_url(self) -> str:
            """
            Returns the download URL for the firmware represented by this FirmwareMeta object.

            Returns:
                str: The download URL for the firmware.
            """
            return f"https://samfw.com/firmware/{self.model}/{self.region}/{self.pda}"

        @staticmethod
        def get_major_version(pda: str) -> int:
            """
            Returns the major version of the Android operating system represented by the given
            PDA string.

            Args:
                pda (str): The PDA string representing the firmware version.

            Returns:
                int: The major version of the Android operating system.
            """
            return int(pda[-4])

        @staticmethod
        def get_build_date1(pda: str) -> int:
            """
            Returns the build date of the firmware version represented by the given PDA string.

            Args:
                pda (str): The PDA string representing the firmware version.

            Returns:
                int: The build date of the firmware version.
            """
            return int(pda[-3])

        @staticmethod
        def get_build_date2(pda: str) -> int:
            """
            Returns the build date of the firmware version represented by the given PDA string.

            Args:
                pda (str): The PDA string representing the firmware version.

            Returns:
                int: The build date of the firmware version.
            """
            return int(pda[-2])

        @staticmethod
        def get_minor_version(pda: str) -> int:
            """
            Returns the minor version of the Android operating system represented by the given PDA
            string.

            Args:
                pda (str): The PDA string representing the firmware version.

            Returns:
                int: The minor version of the Android operating system.
            """
            return int(pda[-1])

        def is_newer_than(self, old_pda) -> bool:
            """
            Determines if the firmware version represented by this FirmwareInfo object is newer
            than the firmware version represented by the given PDA string.

            Args:
                old_pda (str): The PDA string representing the old firmware version.

            Returns:
                bool: True if the firmware version represented by this FirmwareInfo object is newer
                than the firmware version represented by the given PDA string, False otherwise.
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

    async def fetch_latest(self, model: str, region: str) -> FirmwareMeta | None:
        """
        Fetches the latest firmware information for the given model and region.

        Args:
            model (str): The model of the device.
            region (str): The region of the device.

        Returns:
            FirmwareMeta | None: The latest firmware information for the given model and region,
            or None if the information could not be fetched.
        """
        try:
            r = await FWSession.get_device_doc(model, region)
            soup = BeautifulSoup(r.data, "lxml")
            inp = soup.find(id="dflt_page")

            if inp is not None:
                magic = inp["value"].split("/")[3]  # type: ignore

                r = await FWSession.get_device_eng(model, magic)
                soup = BeautifulSoup(r.data, "lxml")

                changelog_entries = soup.find_all(class_="row")
                if len(changelog_entries) >= 2:
                    latest_entry = changelog_entries[1]
                    info = latest_entry.find_all(class_="col-md-3")

                    if len(info) >= 4:
                        pda = info[0].text.split(":")[1].strip()
                        os_version = info[1].text.split(":")[1].strip().replace("(Android ", " (")
                        release_date = info[2].text.split(":")[1].strip()
                        security_patch = info[3].text.split(":")[1].strip()
                        name = ""
                        changelog_txt = ""
                        h1 = soup.find_all("h1")

                        if len(h1) > 0:
                            name = h1[0].text.split("(")[0].strip()

                        changelog_text = soup.find_all("span")

                        if len(changelog_text) > 1:
                            changelog_txt = changelog_text[1].get_text().replace("<br>", "\n")

                        return self.FirmwareMeta(
                            model=model,
                            region=region,
                            os_version=os_version,
                            pda=pda,
                            build_date=datetime.strptime(release_date, DATE_FORMAT),
                            securitypatch=datetime.strptime(security_patch, DATE_FORMAT),
                            name=name,
                            changelog=changelog_txt,
                        )
        except BaseException as e:
            log.error("[SamsungFirmwareInfo] Failed to fetch latest firmware info %s", e)
            return None


FirmwareInfo = SamsungFirmwareInfo()