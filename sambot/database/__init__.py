# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

from .base import SqliteConnection, SqliteDBConn
from .chats import chats_db
from .devices import devices_db
from .firmware import Firmwares
from .users import users_db

__all__ = (
    "SqliteConnection",
    "SqliteDBConn",
    "chats_db",
    "devices_db",
    "Firmwares",
    "users_db",
)


async def create_tables() -> None:
    await chats_db.create_tables()
    await users_db.create_tables()
    await devices_db.create_tables()
    await Firmwares().create_tables()
