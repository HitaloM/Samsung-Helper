# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from sambot import config


class IsSudo(BaseFilter):
    """Check if user is sudo."""

    async def __call__(self, union: Message | CallbackQuery) -> bool:
        is_callback = isinstance(union, CallbackQuery)
        message = union.message if is_callback else union
        if message is None:
            return False

        if union.from_user is None:
            return False

        return union.from_user.id in config.sudoers
