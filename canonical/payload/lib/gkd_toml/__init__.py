# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2021 Taneli Hukkinen
# Licensed to PSF under a Contributor Agreement.

"""TOML parser facade using stdlib tomllib when it is available."""

__all__ = ("loads", "load", "TOMLDecodeError")
__version__ = "2.0.1"

try:
    from tomllib import TOMLDecodeError, load, loads
except ModuleNotFoundError:
    from ._parser import TOMLDecodeError, load, loads

    TOMLDecodeError.__module__ = __name__
