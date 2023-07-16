# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

from pathlib import Path
from typing import Literal

from aiogram.types import User

from sambot import app_dir

from .base import SqliteConnection


class Users(SqliteConnection):
    db_path: Path = app_dir / "sambot/database/primary.db"

    async def create_tables(self) -> None:
        sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            language_code TEXT
        )
        """
        await Users._make_request(self.db_path, sql)

    async def get_user(self, user: User) -> list | str | None:
        sql = "SELECT * FROM users WHERE id = ?"
        params = (user.id,)
        return await Users._make_request(self.db_path, sql, params, fetch=True, mult=True) or None

    async def register_user(self, user: User) -> None:
        sql = "INSERT INTO users (id) VALUES (?)"
        params = (user.id,)
        await Users._make_request(self.db_path, sql, params)

    async def get_language(self, user: User) -> str | None:
        sql = "SELECT language_code FROM users WHERE id = ?"
        params = (user.id,)
        return (await Users._make_request(self.db_path, sql, params, fetch=True) or [None])[0]

    async def set_language(self, user: User, language_code: str) -> None:
        sql = "UPDATE users SET language_code = ? WHERE id = ?"
        params = (language_code, user.id)
        if not await Users.get_user(self, user=user):
            sql = "INSERT INTO users (language_code, id) VALUES (?, ?)"
        await Users._make_request(self.db_path, sql, params)

    async def get_users_count(self, language_code: str | None = None) -> str | Literal[0]:
        sql = "SELECT COUNT(*) FROM users"
        params = ()
        if language_code:
            sql += " WHERE language_code = ?"
            params = (language_code,)
        r = await Users._make_request(self.db_path, sql, params, fetch=True)
        return r[0] if r and r[0] else 0


users_db = Users()
