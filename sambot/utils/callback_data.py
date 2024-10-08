# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from aiogram.filters.callback_data import CallbackData


class StartCallback(CallbackData, prefix="start"):
    menu: str
