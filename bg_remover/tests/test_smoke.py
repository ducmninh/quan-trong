"""Smoke tests that don't require rembg/onnxruntime to be installed.

These verify that the package imports cleanly, that argument parsing works,
and that path-derivation helpers behave as expected. The actual model
inference is exercised manually / in integration tests, not in CI.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bg_remover import (
    DEFAULT_MODEL,
    SUPPORTED_INPUT_EXTS,
    BackgroundRemover,
    iter_image_files,
)
from bg_remover.cli import build_parser
from bg_remover.core import derive_output_path


def test_defaults() -> None:
    assert DEFAULT_MODEL == "u2net"
    assert ".jpg" in SUPPORTED_INPUT_EXTS
    assert ".png" in SUPPORTED_INPUT_EXTS


def test_remover_construction_is_lazy() -> None:
    # Building the dataclass must NOT import rembg.
    remover = BackgroundRemover(model_name="u2net")
    assert remover.model_name == "u2net"
    assert remover._session is None  # noqa: SLF001 — intentional white-box check


def test_cli_parser_help() -> None:
    parser = build_parser()
    args = parser.parse_args(["input.jpg", "-o", "out.png"])
    assert args.input == Path("input.jpg")
    assert args.output == Path("out.png")
    assert args.model == DEFAULT_MODEL
    assert args.alpha_matting is False
    assert args.recursive is False


def test_cli_parser_requires_output() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["input.jpg"])


def test_iter_image_files(tmp_path: Path) -> None:
    (tmp_path / "a.jpg").write_bytes(b"x")
    (tmp_path / "b.PNG").write_bytes(b"x")
    (tmp_path / "c.txt").write_bytes(b"x")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "d.jpeg").write_bytes(b"x")

    flat = sorted(p.name for p in iter_image_files(tmp_path, recursive=False))
    assert flat == ["a.jpg", "b.PNG"]

    deep = sorted(p.name for p in iter_image_files(tmp_path, recursive=True))
    assert deep == ["a.jpg", "b.PNG", "d.jpeg"]


def test_iter_image_files_single_file(tmp_path: Path) -> None:
    f = tmp_path / "only.jpg"
    f.write_bytes(b"x")
    assert list(iter_image_files(f)) == [f]


def test_derive_output_path_flat(tmp_path: Path) -> None:
    src = tmp_path / "photo.jpg"
    dst = derive_output_path(src, tmp_path / "out")
    assert dst == tmp_path / "out" / "photo.png"


def test_derive_output_path_with_suffix(tmp_path: Path) -> None:
    src = tmp_path / "photo.jpg"
    dst = derive_output_path(src, tmp_path / "out", suffix="_nobg")
    assert dst == tmp_path / "out" / "photo_nobg.png"


def test_derive_output_path_preserves_subdirs(tmp_path: Path) -> None:
    root = tmp_path / "in"
    root.mkdir()
    sub = root / "sub"
    sub.mkdir()
    src = sub / "photo.jpg"
    src.write_bytes(b"x")
    dst = derive_output_path(src, tmp_path / "out", src_root=root)
    assert dst == tmp_path / "out" / "sub" / "photo.png"
