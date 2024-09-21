# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from pathlib import Path

from sambot import app_dir
from sambot.database.base import SqliteConnection


class Devices(SqliteConnection):
    db_path: Path = app_dir / "sambot/database/devices.db"

    async def create_tables(self) -> None:
        sql = """
        CREATE TABLE IF NOT EXISTS devices (
            DeviceID INTEGER PRIMARY KEY,
            Name TEXT,
            URL TEXT,
            ImgURL TEXT,
            ShortDescription TEXT
        );
        CREATE TABLE IF NOT EXISTS models (
            DeviceID INTEGER,
            Model TEXT PRIMARY KEY,
            FOREIGN KEY (DeviceID) REFERENCES devices(DeviceID)
        );
        CREATE TABLE IF NOT EXISTS regions (
            Model TEXT,
            Region TEXT,
            FOREIGN KEY (Model) REFERENCES models(Model)
        );
        CREATE TABLE IF NOT EXISTS details (
            DeviceID INTEGER,
            Category TEXT,
            Name TEXT,
            Value TEXT,
            FOREIGN KEY (DeviceID) REFERENCES devices(DeviceID)
        );
        """

        for statement in sql.strip().split(";"):
            if statement.strip():
                await self._make_request(self.db_path, statement)

    async def save(self, device) -> list | str | None:
        # Delete old data
        model = await self._make_request(
            self.db_path, "SELECT Model FROM models WHERE DeviceID = ?", (device.id,), fetch=True
        )

        if model:
            await self._make_request(
                self.db_path, "DELETE FROM regions WHERE Model = ?", (model[0],)
            )

        await self._make_request(
            self.db_path,
            """
            DELETE FROM details WHERE DeviceID = ?;
            DELETE FROM models WHERE DeviceID = ?;
            DELETE FROM devices WHERE DeviceID = ?;
            """,
            (device.id, device.id, device.id),
        )

        # Insert new data
        await self._make_request(
            self.db_path,
            """
            INSERT OR REPLACE INTO devices (DeviceID, Name, URL, ImgURL, ShortDescription)
            VALUES (?, ?, ?, ?, ?)
            """,
            (device.id, device.name, device.url, device.img_url, device.short_description),
        )

        for model in device.models:
            await self._make_request(
                self.db_path,
                "INSERT OR REPLACE INTO models (DeviceID, Model) VALUES (?, ?)",
                (device.id, model),
            )

        for model, regions in device.regions.items():
            for region in regions:
                await self._make_request(
                    self.db_path,
                    "INSERT OR REPLACE INTO regions (Model, Region) VALUES (?, ?)",
                    (model, region),
                )

        for category, details in device.details.items():
            for name, value in details.items():
                await self._make_request(
                    self.db_path,
                    """
                    INSERT OR REPLACE INTO details (DeviceID, Category, Name, Value)
                    VALUES (?, ?, ?, ?)
                    """,
                    (device.id, category, name, value),
                )

    async def get_all_models(self) -> list | str | None:
        result = await self._make_request(
            self.db_path, "SELECT Model FROM models", fetch=True, mult=True
        )
        return [row[0] for row in result] if result else None

    async def get_regions_by_model(self, model: str) -> list | str | None:
        result = await self._make_request(
            self.db_path,
            "SELECT Region FROM regions WHERE Model = ?",
            (model,),
            fetch=True,
            mult=True,
        )
        return [row[0] for row in result] if result else None

    async def search_devices(self, query: str) -> list | str | None:
        sql = """
        SELECT * FROM devices
        WHERE Name LIKE ? OR DeviceID IN (
            SELECT DeviceID FROM models WHERE Model LIKE ?
        )
        """
        params = (f"%{query}%", f"%{query}%")
        return await self._make_request(self.db_path, sql, params, fetch=True, mult=True)

    async def get_device_by_id(self, device_id: int) -> list | str | None:
        return await self._make_request(
            self.db_path, "SELECT * FROM devices WHERE DeviceID = ?", (device_id,), fetch=True
        )

    async def get_specs_by_id(self, device_id: int) -> list | str | None:
        return await self._make_request(
            self.db_path,
            "SELECT * FROM details WHERE DeviceID = ?",
            (device_id,),
            fetch=True,
            mult=True,
        )
