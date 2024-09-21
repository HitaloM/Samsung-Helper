# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from operator import itemgetter

get_major_version = itemgetter(-4)
get_build_year = itemgetter(-3)
get_build_month = itemgetter(-2)
get_build_id = itemgetter(-1)
