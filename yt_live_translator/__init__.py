"""Source checkout import shim for the yt_live_translator package.

The implementation package lives under `src/yt_live_translator`. This shim lets
`python -m yt_live_translator.main` work from the repository root before the
project is installed in editable mode.
"""

from __future__ import annotations

from pathlib import Path


__all__ = ["__version__"]

__version__ = "0.1.0"

_SRC_PACKAGE = Path(__file__).resolve().parent.parent / "src" / "yt_live_translator"

if _SRC_PACKAGE.is_dir():
    __path__.append(str(_SRC_PACKAGE))
