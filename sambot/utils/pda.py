# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>


def get_major_version(pda: str) -> str | int:
    """
    Returns the major version of the Android operating system represented by the given
    PDA string.

    Args:
        pda (str): The PDA string representing the firmware version.

    Returns:
        str: The major version of the Android operating system.
    """
    return pda[-4]


def get_build_year(pda: str) -> str | int:
    """
    Returns the build date of the firmware version represented by the given PDA string.

    Args:
        pda (str): The PDA string representing the firmware version.

    Returns:
        str: The build date of the firmware version.
    """
    return pda[-3]


def get_build_month(pda: str) -> str | int:
    """
    Returns the build date of the firmware version represented by the given PDA string.

    Args:
        pda (str): The PDA string representing the firmware version.

    Returns:
        str: The build date of the firmware version.
    """
    return pda[-2]


def get_build_id(pda: str) -> str | int:
    """
    Returns the minor version of the Android operating system represented by the given PDA
    string.

    Args:
        pda (str): The PDA string representing the firmware version.

    Returns:
        str: The minor version of the Android operating system.
    """
    return pda[-1]
