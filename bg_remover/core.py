"""Core background-removal helpers.

The heavy `rembg` / `onnxruntime` dependencies are imported lazily so that
this module (and the rest of the package) can be imported even when those
extras have not been installed yet — useful for unit tests and `--help`.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional

# Generic / portrait-friendly default. See https://github.com/danielgatis/rembg
# for the full list of supported models (u2net, isnet-general-use, isnet-anime,
# silueta, sam, birefnet-*, ...).
DEFAULT_MODEL = "u2net"

SUPPORTED_INPUT_EXTS = frozenset(
    {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
)


def _lazy_new_session(model_name: str):
    """Import rembg lazily and build a session for *model_name*."""
    try:
        from rembg import new_session  # type: ignore import-not-found
    except ImportError as exc:  # pragma: no cover - exercised at runtime
        raise RuntimeError(
            "The 'rembg' package is required for background removal. "
            "Install it with: pip install -r bg_remover/requirements.txt"
        ) from exc
    return new_session(model_name)


@dataclass
class BackgroundRemover:
    """Reusable wrapper around a single `rembg` session.

    Reusing the same session across many images avoids reloading the
    underlying ONNX model on every call, which is the slow part.
    """

    model_name: str = DEFAULT_MODEL
    alpha_matting: bool = False
    alpha_matting_foreground_threshold: int = 240
    alpha_matting_background_threshold: int = 10
    alpha_matting_erode_size: int = 10
    post_process_mask: bool = False
    only_mask: bool = False
    bgcolor: Optional[tuple[int, int, int, int]] = None

    def __post_init__(self) -> None:
        self._session = None  # built lazily on first use

    def _session_or_init(self):
        if self._session is None:
            self._session = _lazy_new_session(self.model_name)
        return self._session

    def process_bytes(self, data: bytes) -> bytes:
        """Return PNG bytes with the background removed."""
        try:
            from rembg import remove  # type: ignore import-not-found
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "The 'rembg' package is required for background removal."
            ) from exc

        return remove(
            data,
            session=self._session_or_init(),
            alpha_matting=self.alpha_matting,
            alpha_matting_foreground_threshold=self.alpha_matting_foreground_threshold,
            alpha_matting_background_threshold=self.alpha_matting_background_threshold,
            alpha_matting_erode_size=self.alpha_matting_erode_size,
            post_process_mask=self.post_process_mask,
            only_mask=self.only_mask,
            bgcolor=self.bgcolor,
        )

    def process_file(self, src: Path, dst: Path) -> Path:
        """Read *src*, remove its background, write the result to *dst*."""
        src = Path(src)
        dst = Path(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        output = self.process_bytes(src.read_bytes())
        dst.write_bytes(output)
        return dst

    def process_pil(self, image):
        """Process a PIL image and return a new PIL image (RGBA)."""
        from PIL import Image  # local import keeps top-level light

        buf = io.BytesIO()
        # Save as PNG to preserve any existing alpha; rembg accepts most formats.
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGBA")
        image.save(buf, format="PNG")
        out = self.process_bytes(buf.getvalue())
        return Image.open(io.BytesIO(out)).convert("RGBA")


def iter_image_files(root: Path, recursive: bool = False) -> Iterator[Path]:
    """Yield image files under *root* whose extension is supported."""
    root = Path(root)
    if root.is_file():
        if root.suffix.lower() in SUPPORTED_INPUT_EXTS:
            yield root
        return
    pattern = "**/*" if recursive else "*"
    for path in sorted(root.glob(pattern)):
        if path.is_file() and path.suffix.lower() in SUPPORTED_INPUT_EXTS:
            yield path


def remove_background(
    src: Path | str,
    dst: Path | str,
    *,
    model: str = DEFAULT_MODEL,
    alpha_matting: bool = False,
) -> Path:
    """One-shot helper: remove the background from a single file."""
    remover = BackgroundRemover(model_name=model, alpha_matting=alpha_matting)
    return remover.process_file(Path(src), Path(dst))


def remove_background_bytes(
    data: bytes,
    *,
    model: str = DEFAULT_MODEL,
    alpha_matting: bool = False,
) -> bytes:
    """One-shot helper for in-memory image bytes."""
    remover = BackgroundRemover(model_name=model, alpha_matting=alpha_matting)
    return remover.process_bytes(data)


def derive_output_path(
    src: Path,
    out_dir: Path,
    *,
    src_root: Optional[Path] = None,
    suffix: str = "",
) -> Path:
    """Build the output path for *src* under *out_dir*.

    When *src_root* is given, the file's path relative to *src_root* is
    preserved under *out_dir* (useful for `--recursive`).
    The output is always written as PNG so transparency is preserved.
    """
    src = Path(src)
    out_dir = Path(out_dir)
    if src_root is not None:
        try:
            rel = src.relative_to(src_root)
        except ValueError:
            rel = Path(src.name)
    else:
        rel = Path(src.name)
    stem = rel.stem + suffix
    return out_dir / rel.with_name(stem + ".png")


def process_paths(
    inputs: Iterable[Path],
    out_dir: Path,
    *,
    model: str = DEFAULT_MODEL,
    alpha_matting: bool = False,
    suffix: str = "",
    src_root: Optional[Path] = None,
    on_progress=None,
) -> list[Path]:
    """Process many files with a single shared session. Returns output paths."""
    remover = BackgroundRemover(model_name=model, alpha_matting=alpha_matting)
    results: list[Path] = []
    inputs_list = list(inputs)
    total = len(inputs_list)
    for index, src in enumerate(inputs_list, start=1):
        dst = derive_output_path(src, out_dir, src_root=src_root, suffix=suffix)
        remover.process_file(src, dst)
        results.append(dst)
        if on_progress is not None:
            on_progress(index, total, src, dst)
    return results
