# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

from pathlib import Path

from sambot import app_dir

from .base import SqliteConnection


class Firmwares(SqliteConnection):
    def __init__(
        self,
        db_path: Path = app_dir / "sambot/database/firmwares.db",
    ) -> None:
        self.db_path = db_path

    async def create_tables(self) -> None:
        sql = "CREATE TABLE IF NOT EXISTS pda (Model varchar(255), PDA varchar(255))"
        await Firmwares._make_request(self.db_path, sql)

    async def get_pda(self, model: str) -> list | str | None:
        sql = "SELECT PDA FROM pda WHERE Model LIKE ?"
        params = (model,)
        r = await Firmwares._make_request(self.db_path, sql, params, fetch=True)
        return r[0] if r and r[0] else None

    async def check_model_exists(self, model: str) -> bool:
        sql = "SELECT PDA FROM pda WHERE Model LIKE ?"
        params = (model,)
        r = await Firmwares._make_request(self.db_path, sql, params, fetch=True)
        return bool(r)

    async def set_pda(self, model: str, pda: str) -> None:
        if not await Firmwares.check_model_exists(self, model):
            sql = "INSERT INTO pda (Model, PDA) VALUES (?, ?)"
        else:
            sql = "UPDATE pda SET PDA = ? WHERE Model LIKE ?"
        params = (pda, model)
        await Firmwares._make_request(self.db_path, sql, params)
