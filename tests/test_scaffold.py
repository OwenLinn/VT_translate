from __future__ import annotations

from yt_live_translator import __version__
from yt_live_translator.main import SCAFFOLD_MESSAGE, main


def test_package_imports() -> None:
    assert __version__ == "0.1.0"


def test_main_prints_scaffold_message(capsys) -> None:
    assert main([]) == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == SCAFFOLD_MESSAGE
