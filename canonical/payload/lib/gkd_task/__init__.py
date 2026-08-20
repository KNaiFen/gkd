"""Deterministic task coordination for the GKD development bundle."""

import sys

sys.dont_write_bytecode = True

from .errors import TaskError


__all__ = ["TaskError"]
