# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

from pathlib import Path

from sambot import app_dir
from sambot.utils.scraper import SamsungDeviceScraper

from .base import SqliteConnection


class Devices(SqliteConnection):
    db_path: Path = app_dir / "sambot/database/devices.sqlite3"

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
        await Devices._make_request(self.db_path, sql)

    async def save(self, device: SamsungDeviceScraper.DeviceMeta) -> list | str | None:
        # delete old data
        sql = "SELECT Model FROM models WHERE DeviceID = ?"
        params = (device.id,)
        model = await Devices._make_request(self.db_path, sql, params)

        sql = "DELETE FROM regions WHERE Model = ?"
        params = (model,)
        await Devices._make_request(self.db_path, sql, params)

        sql = """
            DELETE FROM details WHERE DeviceID = ?;
            DELETE FROM models WHERE DeviceID = ?;
            DELETE FROM devices WHERE DeviceID = ?;
        """

        # insert new data
        sql = """
        INSERT INTO devices (DeviceID, Name, URL, ImgURL, ShortDescription)
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
            sql = "INSERT INTO models (DeviceID, Model) VALUES (?, ?)"
            params = (device.id, model)
            await Devices._make_request(self.db_path, sql, params)

        for model in device.regions:
            regions = device.regions.get(model)
            if regions:
                for region in regions:
                    sql = "INSERT INTO regions (Model, Region) VALUES (?, ?)"
                    params = (model, region)
                    await Devices._make_request(self.db_path, sql, params)

        for category in device.details:
            for prop in device.details.get(category, {}):
                sql = "INSERT INTO details (DeviceID, Category, Name, Value) VALUES (?, ?, ?, ?)"
                params = (
                    device.id,
                    category,
                    prop,
                    device.details.get(category, {}).get(prop),
                )
                await Devices._make_request(self.db_path, sql, params)


devices = Devices()
