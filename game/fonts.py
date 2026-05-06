"""Font helper – loads fonts that properly support Vietnamese (Unicode) text.

Uses pygame.font.Font() with direct .ttf file paths instead of SysFont,
which guarantees the correct font file is loaded with full Unicode coverage.
"""
from __future__ import annotations

import os
from functools import lru_cache

import pygame

# Ordered list of (regular, bold) .ttf paths – first existing pair wins.
_FONT_CANDIDATES = [
    # Segoe UI – best Unicode coverage on Windows
    (r"C:\Windows\Fonts\segoeui.ttf",  r"C:\Windows\Fonts\segoeuib.ttf"),
    # Arial – also full Unicode on Windows
    (r"C:\Windows\Fonts\arial.ttf",    r"C:\Windows\Fonts\arialbd.ttf"),
    # Tahoma
    (r"C:\Windows\Fonts\tahoma.ttf",   r"C:\Windows\Fonts\tahomabd.ttf"),
    # Calibri
    (r"C:\Windows\Fonts\calibri.ttf",  r"C:\Windows\Fonts\calibrib.ttf"),
    # Verdana
    (r"C:\Windows\Fonts\verdana.ttf",  r"C:\Windows\Fonts\verdanab.ttf"),
    # Linux / Mac fallbacks
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]

_regular_path: str | None = None
_bold_path: str | None = None


def _init_paths() -> None:
    global _regular_path, _bold_path
    if _regular_path is not None:
        return
    for reg, bold in _FONT_CANDIDATES:
        if os.path.isfile(reg):
            _regular_path = reg
            _bold_path = bold if os.path.isfile(bold) else reg
            return
    # absolute last resort – pygame built-in (no Vietnamese but won't crash)
    _regular_path = ""
    _bold_path = ""


@lru_cache(maxsize=32)
def get(size: int, bold: bool = False) -> pygame.font.Font:
    """Return a pygame Font that can render Vietnamese text at *size* px."""
    _init_paths()
    path = _bold_path if bold else _regular_path
    if path:
        try:
            return pygame.font.Font(path, size)
        except Exception:
            pass
    # fallback to pygame default
    return pygame.font.SysFont(None, size)
