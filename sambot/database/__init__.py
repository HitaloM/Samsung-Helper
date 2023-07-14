# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

from .base import SqliteConnection, SqliteDBConn
from .chats import chats
from .devices import devices
from .users import users

__all__ = ("SqliteConnection", "SqliteDBConn", "chats", "devices", "users")


async def create_tables() -> None:
    await chats.create_tables()
    await users.create_tables()
    await devices.create_tables()
