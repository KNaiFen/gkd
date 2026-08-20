"""Remove the startup cache created before bytecode writes were disabled."""

from pathlib import Path
import sitecustomize


cache = Path(sitecustomize.__cached__)
cache.unlink(missing_ok=True)
if cache.parent.is_dir() and not any(cache.parent.iterdir()):
    cache.parent.rmdir()
