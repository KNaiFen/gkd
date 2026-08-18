"""Stable task-core errors."""


class TaskError(Exception):
    """A path-free, credential-free machine error."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code
