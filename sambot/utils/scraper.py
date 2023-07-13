# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>


class SamsungDeviceScrapper:
    GSMARENA_BASE_URL: str = "https://www.gsmarena.com/"
    SAMFW_BASE_URL: str = "https://samfw.com/"
    DEVICES_LIST_URL: str = GSMARENA_BASE_URL + "samsung-phones-f-9-0-p%d.php"
    REGIONS_URL: str = SAMFW_BASE_URL + "firmware/%s"
    FETCH_TIMEOUT: int = 1 * 60 * 1000
    FETCH_INTERVAL: int = 3 * 1000
