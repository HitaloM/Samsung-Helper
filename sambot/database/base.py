# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

from pathlib import Path
from types import TracebackType
from typing import Any, TypeVar

import aiosqlite

from sambot.utils.logging import log

T = TypeVar("T")


class SqliteDBConn:
    def __init__(self, db_name: Path) -> None:
        self.db_name = db_name

    async def __aenter__(self) -> aiosqlite.Connection:
        self.conn = await aiosqlite.connect(self.db_name)
        self.conn.row_factory = aiosqlite.Row
        return self.conn

    async def __aexit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.conn.close()
        if exc_val:
            raise exc_val


class SqliteConnection:
    @staticmethod
    async def __make_request(
        db: Path,
        sql: str,
        params: list[tuple] | tuple = (),
        fetch: bool = False,
        mult: bool = False,
    ) -> Any:
        async with SqliteDBConn(db) as conn:
            try:
                if ";" in sql:
                    await conn.executescript(sql)
                else:
                    cursor = (
                        await conn.executemany(sql, params)
                        if isinstance(params, list)
                        else await conn.execute(sql, params)
                    )
                    if fetch:
                        return await cursor.fetchall() if mult else await cursor.fetchone()
                    await conn.commit()
            except BaseException:
                log.error(
                    "[SqliteConnection] - Failed to execute query!",
                    sql=sql,
                    params=params,
                    exc_info=True,
                )

    @staticmethod
    def _convert_to_model(data: dict, model: type[T]) -> T:
        return model(**data)

    @staticmethod
    async def _make_request(
        db: Path,
        sql: str,
        params: tuple = (),
        fetch: bool = False,
        mult: bool = False,
        model_type: type[T] | None = None,
    ) -> T | list[T] | str | None:
        raw = await SqliteConnection.__make_request(db, sql, params, fetch, mult)
        if raw is None:
            return [] if mult else None
        if mult:
            return (
                [SqliteConnection._convert_to_model(i, model_type) for i in raw]
                if model_type is not None
                else list(raw)
            )
        return (
            SqliteConnection._convert_to_model(raw, model_type) if model_type is not None else raw
        )


async def run_vacuum(db: Path) -> None:
    async with SqliteDBConn(db) as conn:
        await conn.execute("VACUUM")
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.commit()
