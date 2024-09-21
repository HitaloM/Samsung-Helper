# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from pathlib import Path

from sambot import app_dir
from sambot.database.base import SqliteConnection


class Firmwares(SqliteConnection):
    def __init__(self, db_path: Path = app_dir / "sambot/database/firmwares.db") -> None:
        self.db_path = db_path

    async def create_tables(self) -> None:
        sql = """
        CREATE TABLE IF NOT EXISTS pda (
            Model TEXT PRIMARY KEY,
            PDA TEXT
        )
        """
        await self._make_request(self.db_path, sql)

    async def get_pda(self, model: str) -> str | None:
        sql = "SELECT PDA FROM pda WHERE Model = ?"
        params = (model,)
        result = await self._make_request(self.db_path, sql, params, fetch=True)
        return result[0] if result else None

    async def check_model_exists(self, model: str) -> bool:
        sql = "SELECT 1 FROM pda WHERE Model = ?"
        params = (model,)
        result = await self._make_request(self.db_path, sql, params, fetch=True)
        return bool(result)

    async def set_pda(self, model: str, pda: str) -> None:
        if await self.check_model_exists(model):
            sql = "UPDATE pda SET PDA = ? WHERE Model = ?"
        else:
            sql = "INSERT INTO pda (Model, PDA) VALUES (?, ?)"
        params = (model, pda) if "INSERT" in sql else (pda, model)
        await self._make_request(self.db_path, sql, params)
