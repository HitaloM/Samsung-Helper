# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
from dataclasses import dataclass, field

from bs4 import BeautifulSoup

from sambot.database.devices import Devices
from sambot.utils.aiohttp import GSMClient
from sambot.utils.aiohttp.devices import RegionsClient
from sambot.utils.logging import log


@dataclass(slots=True)
class DeviceMeta:
    id: int = -1
    name: str | None = None
    url: str | None = None
    img_url: str | None = None
    short_description: str | None = None
    details: dict[str, dict[str, str]] = field(default_factory=dict)
    model_supername: str | None = None
    models: list[str] = field(default_factory=list)
    regions: dict[str, set[str]] = field(default_factory=dict)

    def raw(self) -> dict:
        return self.__dict__

    def __str__(self) -> str:
        return str(self.raw())


async def fetch_page(page: int) -> list[DeviceMeta]:
    devices_list = await GSMClient.get_devices_list(page)
    soup = BeautifulSoup(devices_list, "lxml")
    elements = soup.select("#review-body > div.makers > ul > li")

    device_list = []
    for element in elements:
        device = DeviceMeta(
            name=element.select("a > strong > span")[0].text,
            url=element.select("a")[0].attrs["href"],
            id=int(element.select("a")[0].attrs["href"].split("-")[-1].split(".php")[0]),
            img_url=element.select("a > img")[0].attrs["src"],
            short_description=element.select("a > img")[0].attrs["title"],
        )
        device_list.append(device)

    return device_list


def get_normalized_models(device_meta: DeviceMeta) -> set[str]:
    models = device_meta.details.get("Misc", {}).get("Models", "")
    split_models = models.split(",")

    models_set = {model.strip().split("/")[0] for model in split_models}
    return {model for model in models_set if model.startswith("SM-")}


def get_model_supername(device_meta: DeviceMeta) -> str:
    if not device_meta.models:
        return ""
    if len(device_meta.models) == 1:
        return device_meta.models[0]
    return device_meta.models[0][
        : next(
            (
                i
                for i, (x, y) in enumerate(
                    zip(device_meta.models[0], device_meta.models[1:], strict=False)
                )
                if x != y
            ),
            len(device_meta.models[0]),
        )
    ]


def is_device_relevant(device_meta: DeviceMeta) -> bool:
    if not device_meta.details:
        return False

    normalized_models = get_normalized_models(device_meta)
    return bool(normalized_models) and all(model.startswith("SM-") for model in normalized_models)


async def fill_details(device_meta: DeviceMeta) -> DeviceMeta:
    device = await GSMClient.get_device(str(device_meta.url))
    soup = BeautifulSoup(device, "lxml")
    tables = soup.select("#specs-list > table")
    for table in tables:
        category = table.select("table > tr > th")[0].text
        if category:
            table_rows = table.select("table > tr")
            inner_map = device_meta.details.get(category, {})
            for row in table_rows:
                header = row.select_one("td.ttl")
                content = row.select_one("td.nfo")
                if header and content:
                    inner_map[header.get_text()] = content.get_text()
            device_meta.details[category] = inner_map

    normalized_models = get_normalized_models(device_meta)
    device_meta.models.extend(normalized_models)
    device_meta.model_supername = get_model_supername(device_meta)

    tasks = [fetch_regions(device_meta, model) for model in device_meta.models]

    await asyncio.gather(*tasks)
    return device_meta


async def fetch_regions(device_meta: DeviceMeta, model: str):
    try:
        device_regions = await RegionsClient.get_regions(model)
        document = BeautifulSoup(device_regions, "lxml")  # type: ignore
        region_elements = document.select(
            "body > div.intro.bg-light > div > div > div > div > "
            "div.card-body.text-justify.card-csc > div.item_csc > a > b"
        )
        region_set = {element.text for element in region_elements}
        device_meta.regions[model] = region_set
    except BaseException:
        log.exception("[DeviceScraper] - Failed to get regions!", model=model)


async def sync_devices() -> None:
    log.info("[DeviceScraper] - Starting device scraping")
    devices_list = await GSMClient.get_devices_list(1)
    doc = BeautifulSoup(devices_list, "lxml")
    try:
        pages_count = int(
            doc.select("#body > div > div.review-nav-v2 > div > a:nth-child(5)")[-1].text
        )
    except Exception:
        log.exception("[DeviceScraper] - Failed to get pages count!")
        return

    log.info("[DeviceScraper] - Found pages of devices.", pages=pages_count)

    devices = []
    log.info("[DeviceScraper] - Fetching pages, please wait...")
    tasks = [fetch_page(i) for i in range(1, pages_count + 1)]
    results = await asyncio.gather(*tasks)
    for result in results:
        devices.extend(result)

    log.info("[DeviceScraper] - Devices found.", count=len(devices))
    devices = [
        device for device in devices if "Galaxy" in device.name and "Watch" not in device.name
    ]
    log.info("[DeviceScraper] - (Stage 1) Filtered devices.", filtered=len(devices))

    details_devices = []
    for i, device in enumerate(devices):
        log.info(
            "[DeviceScraper] - Fetching device details...",
            device=device.name,
            proccess=f"{i + 1}/{len(devices)}",
        )
        device = await fill_details(device)
        details_devices.append(device)

    devices = list(filter(is_device_relevant, details_devices))
    log.info("[DeviceScraper] - (Stage 2) Filtered devices.", filtered=len(devices))
    devices = sorted(devices, key=get_model_supername)

    for device in devices:
        try:
            await Devices().save(device)
            log.info("[DeviceScraper] - Saved device to database.", device=device.name)
        except BaseException:
            log.exception(
                "[DeviceScraper] - Failed to save device to database!", device=device.name
            )
