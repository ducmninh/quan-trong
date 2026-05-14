# bg_remover — Tool xóa phông ảnh bằng Python

Một tool nhỏ gọn để **xóa phông (tách nền) ảnh** bằng Python, dùng thư viện
[`rembg`](https://github.com/danielgatis/rembg) (chạy model AI U²-Net /
ISNet / SAM qua ONNX Runtime — không cần GPU).

Hỗ trợ:

- **CLI**: xử lý 1 ảnh hoặc cả thư mục (kể cả đệ quy).
- **GUI web** (Gradio): kéo-thả ảnh, xem kết quả ngay trên trình duyệt.
- **API Python**: gọi trực tiếp trong code của bạn.

---

## 1. Cài đặt

```bash
# Từ thư mục gốc của repo:
python -m pip install -r bg_remover/requirements.txt
```

Lần đầu chạy, `rembg` sẽ tự tải model (~170MB cho `u2net`) về
`~/.u2net/`. Những lần sau không cần tải lại.

> Không có GPU vẫn chạy tốt — chỉ chậm hơn vài giây/ảnh.

---

## 2. Dùng CLI

### Một ảnh

```bash
python -m bg_remover input.jpg -o output.png
```

### Cả thư mục

```bash
python -m bg_remover ./photos -o ./out
```

### Đệ quy + viền mịn (alpha matting)

```bash
python -m bg_remover ./photos -o ./out --recursive --alpha-matting
```

### Đổi model

`u2net` là mặc định (tốt cho ảnh chung). Một số lựa chọn khác:

| Model               | Phù hợp với                                    |
| ------------------- | ---------------------------------------------- |
| `u2net`             | Mặc định, mục đích chung                       |
| `u2netp`            | Nhẹ hơn, chạy nhanh hơn                        |
| `u2net_human_seg`   | Ảnh người, chân dung                           |
| `isnet-general-use` | Chất lượng cao, mục đích chung                 |
| `isnet-anime`       | Ảnh anime / 2D art                             |
| `silueta`           | Tối ưu kích thước (nhẹ)                        |

```bash
python -m bg_remover portrait.jpg -o portrait_nobg.png --model u2net_human_seg
```

Xem toàn bộ tùy chọn:

```bash
python -m bg_remover --help
```

---

## 3. Dùng GUI (Gradio)

```bash
python -m bg_remover --gui
```

Mở trình duyệt tại <http://localhost:7860> để kéo-thả ảnh.

---

## 4. Dùng như thư viện trong Python

```python
from bg_remover import BackgroundRemover, remove_background

# Cách nhanh nhất: một dòng cho một file.
remove_background("input.jpg", "output.png")

# Cách hiệu quả khi xử lý nhiều ảnh — tái sử dụng cùng một session.
remover = BackgroundRemover(model_name="u2net", alpha_matting=True)
for src in ["a.jpg", "b.jpg", "c.jpg"]:
    remover.process_file(src, f"out/{src.rsplit('.', 1)[0]}.png")
```

Hoặc làm việc với bytes / PIL:

```python
from pathlib import Path
from PIL import Image
from bg_remover import BackgroundRemover

remover = BackgroundRemover()

# Bytes -> bytes
out_bytes = remover.process_bytes(Path("photo.jpg").read_bytes())

# PIL -> PIL (RGBA)
img = Image.open("photo.jpg")
result = remover.process_pil(img)
result.save("photo_nobg.png")
```

---

## 5. Mẹo

- Output luôn được lưu dưới dạng **PNG** để giữ kênh alpha (nền trong suốt).
- Bật `--alpha-matting` giúp viền tóc / lông mịn hơn nhưng chậm hơn.
- Khi xử lý hàng loạt, dùng `BackgroundRemover` (hoặc CLI directory mode)
  để chỉ load model **một lần** — nhanh hơn nhiều so với gọi
  `remove_background()` cho từng ảnh.
