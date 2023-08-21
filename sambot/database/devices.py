# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

from pathlib import Path

from sambot import app_dir

from .base import SqliteConnection


class Devices(SqliteConnection):
    db_path: Path = app_dir / "sambot/database/devices.db"

    async def create_tables(self) -> None:
        sql = """
        CREATE TABLE IF NOT EXISTS devices (
            DeviceID INT,
            Name varchar(255),
            URL varchar(255),
            ImgURL varchar(255),
            ShortDescription varchar(255),
            PRIMARY KEY (DeviceID)
        );
        CREATE TABLE IF NOT EXISTS models (
            DeviceID INT,
            Model varchar(255),
            FOREIGN KEY (DeviceID) REFERENCES devices(DeviceID),
            PRIMARY KEY (Model)
        );
        CREATE TABLE IF NOT EXISTS regions (
            Model varchar(255),
            Region varchar(3),
            FOREIGN KEY (Model) REFERENCES models(Model)
        );
        CREATE TABLE IF NOT EXISTS details (
            DeviceID INT,
            Category varchar(255),
            Name varchar(255),
            Value varchar(255),
            FOREIGN KEY (DeviceID) REFERENCES devices(DeviceID)
        );
        """
        for i in sql.split(";"):
            await Devices._make_request(self.db_path, i)

    async def save(self, device) -> list | str | None:
        # delete old data
        sql = "SELECT Model FROM models WHERE DeviceID = ?"
        params = (device.id,)
        model = await Devices._make_request(self.db_path, sql, params, fetch=True)

        if model:
            sql = "DELETE FROM regions WHERE Model = ?"
            params = (model[0],)
            await Devices._make_request(self.db_path, sql, params)

        sql = """
        DELETE FROM details WHERE DeviceID = ?;
        DELETE FROM models WHERE DeviceID = ?;
        DELETE FROM devices WHERE DeviceID = ?;
        """
        params = (device.id, device.id, device.id)
        await Devices._make_request(self.db_path, sql, params)

        # insert new data
        sql = """
        INSERT OR REPLACE INTO devices (DeviceID, Name, URL, ImgURL, ShortDescription)
        VALUES (?, ?, ?, ?, ?)
        """
        params = (
            device.id,
            device.name,
            device.url,
            device.img_url,
            device.short_description,
        )
        await Devices._make_request(self.db_path, sql, params)

        for model in device.models:
            sql = "INSERT OR REPLACE INTO models (DeviceID, Model) VALUES (?, ?)"
            params = (device.id, model)
            await Devices._make_request(self.db_path, sql, params)

        for model in device.regions:
            regions = device.regions.get(model)
            if regions:
                for region in regions:
                    sql = "INSERT OR REPLACE INTO regions (Model, Region) VALUES (?, ?)"
                    params = (model, region)
                    await Devices._make_request(self.db_path, sql, params)

        for category in device.details:
            for prop in device.details.get(category, {}):
                sql = """
                    INSERT OR REPLACE INTO details (DeviceID, Category, Name, Value)
                    VALUES (?, ?, ?, ?)
                """
                params = (
                    device.id,
                    category,
                    prop,
                    device.details.get(category, {}).get(prop),
                )
                await Devices._make_request(self.db_path, sql, params)

    async def get_all_models(self) -> list | str | None:
        sql = "SELECT Model FROM models"
        r = await Devices._make_request(self.db_path, sql, fetch=True, mult=True)
        return [i[0] for i in r] if r else None

    async def get_regions_by_model(self, model: str) -> list | str | None:
        sql = "SELECT Region FROM regions WHERE Model = ?"
        params = (model,)
        r = await Devices._make_request(self.db_path, sql, params, fetch=True, mult=True)
        return [i[0] for i in r] if r else None

    async def search_devices(self, query: str) -> list | str | None:
        sql = """
        SELECT * FROM devices
        WHERE Name LIKE ? OR DeviceID IN (
            SELECT DeviceID FROM models WHERE Model LIKE ?
        )
        """
        params = (f"%{query}%", f"%{query}%")
        return await Devices._make_request(self.db_path, sql, params, fetch=True, mult=True)

    async def get_device_by_id(self, device_id: int) -> list | str | None:
        sql = "SELECT * FROM devices WHERE DeviceID = ?"
        params = (device_id,)
        return await Devices._make_request(self.db_path, sql, params, fetch=True)

    async def get_specs_by_id(self, device_id: int) -> list | str | None:
        sql = "SELECT * FROM details WHERE DeviceID = ?"
        params = (device_id,)
        return await Devices._make_request(self.db_path, sql, params, fetch=True, mult=True)


devices_db = Devices()
