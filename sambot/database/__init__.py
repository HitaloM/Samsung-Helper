# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

from sambot.database.base import SqliteConnection, SqliteDBConn, run_vacuum
from sambot.database.chats import chats_db
from sambot.database.devices import devices_db
from sambot.database.firmware import Firmwares
from sambot.database.users import users_db

__all__ = (
    "Firmwares",
    "SqliteConnection",
    "SqliteDBConn",
    "chats_db",
    "devices_db",
    "run_vacuum",
    "users_db",
)


async def create_tables() -> None:
    await chats_db.create_tables()
    await users_db.create_tables()
    await devices_db.create_tables()
    await Firmwares().create_tables()
