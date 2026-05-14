"""Optional Gradio web GUI for the background-removal tool.

Run with:
    python -m bg_remover --gui
or:
    python -m bg_remover.gui
"""

from __future__ import annotations

import sys

from .core import DEFAULT_MODEL, BackgroundRemover

# Models worth exposing in the dropdown. Users can still pass any model via
# the CLI; this list is just a sensible default set for the GUI.
GUI_MODELS = [
    "u2net",
    "u2netp",
    "u2net_human_seg",
    "isnet-general-use",
    "isnet-anime",
    "silueta",
]


def _process(image, model_name: str, alpha_matting: bool):
    if image is None:
        return None
    remover = BackgroundRemover(
        model_name=model_name or DEFAULT_MODEL,
        alpha_matting=bool(alpha_matting),
    )
    return remover.process_pil(image)


def build_demo():
    try:
        import gradio as gr  # type: ignore import-not-found
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Gradio is not installed. Install it with: "
            "pip install -r bg_remover/requirements.txt"
        ) from exc

    with gr.Blocks(title="Background Remover") as demo:
        gr.Markdown(
            "# Xóa phông ảnh (Background Remover)\n"
            "Tải lên một ảnh, chọn model rồi nhấn **Run** để tách nền."
        )
        with gr.Row():
            with gr.Column():
                inp = gr.Image(type="pil", label="Ảnh đầu vào / Input")
                model = gr.Dropdown(
                    choices=GUI_MODELS,
                    value=DEFAULT_MODEL,
                    label="Model",
                )
                alpha = gr.Checkbox(
                    value=False,
                    label="Alpha matting (viền sạch hơn, chậm hơn)",
                )
                btn = gr.Button("Run", variant="primary")
            with gr.Column():
                out = gr.Image(
                    type="pil", label="Ảnh đã xóa phông / Output", format="png"
                )

        btn.click(_process, inputs=[inp, model, alpha], outputs=out)

    return demo


def launch_gui(
    server_name: str = "0.0.0.0",
    server_port: int = 7860,
    share: bool = False,
) -> None:
    demo = build_demo()
    demo.launch(server_name=server_name, server_port=server_port, share=share)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(launch_gui() or 0)
