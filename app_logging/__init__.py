"""Structured logging package for MediMind AI.

This package intentionally shares its name with the Python standard library
module. The implementation below proxies the standard library logging API so
third-party dependencies continue to behave normally while the project can also
provide ``logging.logger`` for structured application logging.
"""

from __future__ import annotations

import importlib.util
import sysconfig
from pathlib import Path

_stdlib_logging_path = Path(sysconfig.get_paths()["stdlib"]) / "logging" / "__init__.py"
_stdlib_spec = importlib.util.spec_from_file_location("_stdlib_logging", _stdlib_logging_path)

if _stdlib_spec is None or _stdlib_spec.loader is None:
    raise ImportError("Unable to load the Python standard library logging module")

_stdlib_logging = importlib.util.module_from_spec(_stdlib_spec)
_stdlib_spec.loader.exec_module(_stdlib_logging)

__path__.append(str(_stdlib_logging_path.parent))

for _name in dir(_stdlib_logging):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_stdlib_logging, _name)

__all__ = [name for name in dir(_stdlib_logging) if not name.startswith("_")]

del importlib, sysconfig, Path, _stdlib_logging_path, _stdlib_spec, _stdlib_logging
