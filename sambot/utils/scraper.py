# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

from bs4 import BeautifulSoup

from sambot import GSMSession, RegionsSession
from sambot.database import devices as devices_db
from sambot.utils.logging import log

GSMARENA_URL = "https://www.gsmarena.com/"
DEVICES_LIST_URL = GSMARENA_URL + "samsung-phones-f-9-0-p{}.php"


class SamsungDeviceScraper:
    """
    A class that provides methods to scrape device information from the GSM Arena website.
    """

    class DeviceMeta:
        def __init__(
            self,
            id: int = -1,
            name: str | None = None,
            url: str | None = None,
            img_url: str | None = None,
            short_description: str | None = None,
            details: dict[str, dict[str, str]] = {},
            model_supername: str | None = None,
            models: list[str] = [],
            regions: dict[str, set[str]] = {},
        ):
            self.id = id
            self.name = name
            self.url = url
            self.img_url = img_url
            self.short_description = short_description
            self.details = details
            self.model_supername = model_supername
            self.models = models
            self.regions = regions

        def raw(self) -> dict:
            """
            Returns the raw dictionary representation of the DeviceMeta object.

            Returns:
                dict: A dictionary containing the raw data of the DeviceMeta object.
            """
            return self.__dict__

    @staticmethod
    async def fetch_page(page: int) -> list[DeviceMeta]:
        """
        Retrieves a list of devices from the GSM Arena website for a given page number.

        Args:
            page (int): The page number to retrieve devices from.

        Returns:
            list[DeviceMeta]: A list of DeviceMeta objects representing the devices on the page.
        """
        status, data = await GSMSession.get_devices_list(page)
        soup = BeautifulSoup(data, "lxml")
        elements = soup.select("#review-body > div.makers > ul > li")

        device_list = []
        for element in elements:
            device = DeviceScraper.DeviceMeta(
                name=element.select("a > strong > span")[0].text,
                url=element.select("a")[0].attrs["href"],
                id=int(
                    element.select("a")[0].attrs["href"][
                        element.select("a")[0].attrs["href"].rfind("-")
                        + 1 : element.select("a")[0].attrs["href"].rfind(".php")
                    ]
                ),
                img_url=element.select("a > img")[0].attrs["src"],
                short_description=element.select("a > img")[0].attrs["title"],
            )
            device_list.append(device)

        return device_list

    @staticmethod
    def get_normalized_models(device_meta: DeviceMeta) -> set[str]:
        """
        Returns a set of normalized model names for a given device.

        Args:
            device_meta (DeviceMeta): A DeviceMeta object representing the device.

        Returns:
            set[str]: A set of normalized model names for the device.
        """
        models = device_meta.details.get("Misc", {}).get("Models", "")
        split_models = models.split(",")

        models_set = set()
        for model in split_models:
            models_set.add(model.strip().split("/")[0])

        remove_models = set()
        for model in models_set:
            if not model.startswith("SM-"):
                remove_models.add(model)

        models_set -= remove_models
        return models_set

    @staticmethod
    def get_model_supername(device_meta: DeviceMeta) -> str:
        """
        Returns the supername of a device's model.

        Args:
            device_meta (DeviceMeta): A DeviceMeta object representing the device.

        Returns:
            str: The supername of the device's model.
        """
        if len(device_meta.models) == 0:
            return ""
        return (
            device_meta.models[0]
            if len(device_meta.models) == 1
            else device_meta.models[0][
                : next(
                    (
                        i
                        for i, (x, y) in enumerate(
                            zip(device_meta.models[0], device_meta.models[1:])
                        )
                        if x != y
                    ),
                    len(device_meta.models[0]),
                )
            ]
        )

    def is_device_relevant(self, device_meta: DeviceMeta) -> bool:
        """
        Determines if a device is relevant based on its metadata.

        Args:
            device_meta (DeviceMeta): A DeviceMeta object representing the device.

        Returns:
            bool: True if the device is relevant, False otherwise.
        """
        if len(device_meta.details) == 0:
            return False

        normalized_models = self.get_normalized_models(device_meta)
        if len(normalized_models) == 0:
            return False

        return all(model.startswith("SM-") for model in normalized_models)

    async def fill_details(self, device_meta: DeviceMeta) -> DeviceMeta:
        """
        Fills the details of a device by scraping its page on GSMArena.

        Args:
            device_meta (DeviceMeta): A DeviceMeta object representing the device.

        Returns:
            DeviceMeta: The DeviceMeta object with the filled details.
        """
        status, data = await GSMSession.get_device(str(device_meta.url))
        soup = BeautifulSoup(data, "lxml")
        tables = soup.select("#specs-list > table")
        for table in tables:
            category = table.select_one("tbody > tr:nth-child(1) > th")
            if category:
                category = category.get_text()
                table_rows = table.select("tbody > tr")
                inner_map = device_meta.details.get(category, {})
                for row in table_rows:
                    header = row.select_one("td.ttl")
                    content = row.select_one("td.nfo")
                    if header and content:
                        inner_map[header.get_text()] = content.get_text()
                device_meta.details[category] = inner_map

        normalized_models = self.get_normalized_models(device_meta)
        device_meta.models.extend(normalized_models)
        device_meta.model_supername = self.get_model_supername(device_meta)
        for model in device_meta.models:
            try:
                status, data = await RegionsSession.get_regions(model)
                document = BeautifulSoup(data, "lxml")
                region_elements = document.select(
                    "body > div.intro.bg-light > div > div > div > div > "
                    "div.card-body.text-justify.card-csc > div.item_csc > a > b"
                )
                region_set = {element.text for element in region_elements}
                device_meta.regions[model] = region_set
            except Exception as e:
                log.error("Failed to get regions for model %s: %s", model, e)

        return device_meta

    async def start_scraping(self) -> None:
        status, data = await GSMSession.get_devices_list(1)
        doc = BeautifulSoup(data, "lxml")
        pages_count = int(
            doc.select("#body > div > div.review-nav.pullNeg.col.pushT10 > div.nav-pages > a")[
                -1
            ].text
        )
        log.info("[DeviceScraper] - Found %d pages of devices", pages_count)

        devices = []
        for i in range(1, pages_count + 1):
            device_meta = self.fetch_page(i)
            devices.append(device_meta)

        log.info("[DeviceScraper] - %d total devices", len(devices))
        devices = [
            device for device in devices if "Galaxy" in device.name and "Watch" not in device.name
        ]
        log.info("[DeviceScraper] - %d filtered devices (Stage 1)", len(devices))
        for i in range(len(devices)):
            device = devices[i]
            log.info(
                "[DeviceScraper] - Fetching device details for %s (%d/%d)",
                device.name,
                i + 1,
                len(devices),
            )
            await self.fill_details(device)

        devices = list(filter(self.is_device_relevant, devices))
        log.info("[DeviceScraper] - %d filtered devices (Stage 2)", len(devices))
        devices = sorted(devices, key=lambda x: self.get_model_supername(x))

        try:
            for device in devices:
                await devices_db.save(device)
        except BaseException as e:
            log.error("[DeviceScraper] - Failed to save devices to database: %s", e)


DeviceScraper = SamsungDeviceScraper()
