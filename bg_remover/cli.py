"""Command-line interface for the background-removal tool.

Examples
--------
Single file:
    python -m bg_remover input.jpg -o output.png

Whole folder (non-recursive, writes results into ./out/):
    python -m bg_remover ./photos -o ./out

Recursive, with alpha matting for cleaner edges:
    python -m bg_remover ./photos -o ./out --recursive --alpha-matting

Pick a different model (e.g. for anime art):
    python -m bg_remover input.png -o output.png --model isnet-anime
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import (
    DEFAULT_MODEL,
    BackgroundRemover,
    derive_output_path,
    iter_image_files,
    process_paths,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bg_remover",
        description="Remove image backgrounds using rembg (U^2-Net).",
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to an image file or a directory of images.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help=(
            "Output file (when INPUT is a file) or output directory "
            "(when INPUT is a directory)."
        ),
    )
    parser.add_argument(
        "-m",
        "--model",
        default=DEFAULT_MODEL,
        help=(
            "rembg model name. Examples: u2net (default), u2netp, "
            "u2net_human_seg, isnet-general-use, isnet-anime, silueta."
        ),
    )
    parser.add_argument(
        "--alpha-matting",
        action="store_true",
        help="Enable alpha matting for cleaner edges (slower).",
    )
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="When INPUT is a directory, recurse into sub-directories.",
    )
    parser.add_argument(
        "--suffix",
        default="",
        help="Append this string to each output filename's stem (e.g. '_nobg').",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the Gradio web GUI instead of running the CLI.",
    )
    return parser


def _run_gui() -> int:
    try:
        from .gui import launch_gui
    except ImportError as exc:
        print(f"Failed to import GUI module: {exc}", file=sys.stderr)
        return 2
    launch_gui()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    # Allow `python -m bg_remover --gui` without requiring a positional input.
    if argv is None:
        argv = sys.argv[1:]
    if "--gui" in argv and not any(not a.startswith("-") for a in argv):
        # No positional input -> add a placeholder so argparse is happy.
        argv = ["__gui__", *argv]
    args = parser.parse_args(argv)

    if args.gui:
        return _run_gui()

    input_path: Path = args.input
    output_path: Path = args.output

    if not input_path.exists():
        print(f"error: input path does not exist: {input_path}", file=sys.stderr)
        return 2

    if input_path.is_file():
        # Output is a file path. Force .png so transparency is preserved.
        if output_path.suffix.lower() != ".png":
            print(
                f"note: forcing output suffix to .png (was {output_path.suffix!r})",
                file=sys.stderr,
            )
            output_path = output_path.with_suffix(".png")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        remover = BackgroundRemover(
            model_name=args.model, alpha_matting=args.alpha_matting
        )
        print(f"Processing {input_path} -> {output_path} ...")
        remover.process_file(input_path, output_path)
        print("Done.")
        return 0

    # Directory mode.
    files = list(iter_image_files(input_path, recursive=args.recursive))
    if not files:
        print(f"No supported images found under {input_path}", file=sys.stderr)
        return 1
    output_path.mkdir(parents=True, exist_ok=True)

    def _progress(i: int, total: int, src: Path, dst: Path) -> None:
        print(f"[{i}/{total}] {src} -> {dst}")

    process_paths(
        files,
        output_path,
        model=args.model,
        alpha_matting=args.alpha_matting,
        suffix=args.suffix,
        src_root=input_path,
        on_progress=_progress,
    )
    print(f"Done. Wrote {len(files)} file(s) to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
