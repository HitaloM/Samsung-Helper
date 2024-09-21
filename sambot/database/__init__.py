# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from sambot.database.base import run_vacuum
from sambot.database.devices import Devices
from sambot.database.firmware import Firmwares

__all__ = ("Devices", "Firmwares", "run_vacuum")


async def create_tables() -> None:
    await Devices().create_tables()
    await Firmwares().create_tables()
