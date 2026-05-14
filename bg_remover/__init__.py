"""Background removal tool.

A small Python tool to remove image backgrounds using the rembg library
(U^2-Net based AI models). Supports single files, batch directories,
and an optional Gradio web GUI.
"""

from __future__ import annotations

from .core import (
    DEFAULT_MODEL,
    SUPPORTED_INPUT_EXTS,
    BackgroundRemover,
    remove_background,
    remove_background_bytes,
    iter_image_files,
)

__all__ = [
    "DEFAULT_MODEL",
    "SUPPORTED_INPUT_EXTS",
    "BackgroundRemover",
    "remove_background",
    "remove_background_bytes",
    "iter_image_files",
]
