# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

from pathlib import Path
from typing import Literal

from aiogram.types import Chat

from sambot import app_dir

from .base import SqliteConnection


class Chats(SqliteConnection):
    db_path: Path = app_dir / "sambot/database/primary.sqlite3"

    async def create_tables(self) -> None:
        sql = """
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY,
            language_code TEXT
        )
        """
        await Chats._make_request(self.db_path, sql)

    async def get_chat(self, chat: Chat) -> list | str | None:
        sql = "SELECT * FROM chats WHERE id = ?"
        params = (chat.id,)
        return await Chats._make_request(self.db_path, sql, params, fetch=True, mult=True) or None

    async def register_chat(self, chat: Chat) -> None:
        sql = "INSERT INTO chats (id) VALUES (?)"
        params = (chat.id,)
        await Chats._make_request(self.db_path, sql, params)

    async def get_language(self, chat: Chat) -> str | None:
        sql = "SELECT language_code FROM chats WHERE id = ?"
        params = (chat.id,)
        r = await Chats._make_request(self.db_path, sql, params, fetch=True)
        return r[0] if r and r[0] else None

    async def set_language(self, chat: Chat, language_code: str) -> None:
        sql = "UPDATE chats SET language_code = ? WHERE id = ?"
        params = (language_code, chat.id)
        if not await Chats.get_chat(self, chat):
            sql = "INSERT INTO chats (language_code, id) VALUES (?, ?)"
        await Chats._make_request(self.db_path, sql, params)

    async def get_chats_count(self, language_code: str | None = None) -> str | Literal[0]:
        sql = "SELECT COUNT(*) FROM chats"
        params = ()
        if language_code:
            sql += " WHERE language_code = ?"
            params = (language_code,)
        r = await Chats._make_request(self.db_path, sql, params, fetch=True)
        return r[0] if r and r[0] else 0


chats = Chats()
