"""Quita el fondo a la foto de un speaker y guarda un PNG transparente recortado.

Uso:
    python quitar_fondo.py foto.jpg salida.png

Modelo: u2net_human_seg.onnx (rembg) en ~/.u2net/. Solo necesita onnxruntime, numpy y Pillow.
"""
import sys
from pathlib import Path

import numpy as np
import onnxruntime as ort
from PIL import Image, ImageFilter

MODEL = Path.home() / ".u2net" / "u2net_human_seg.onnx"
SIZE = 320


def mask_for(img: Image.Image) -> Image.Image:
    sess = ort.InferenceSession(str(MODEL), providers=["CPUExecutionProvider"])
    x = np.asarray(img.convert("RGB").resize((SIZE, SIZE), Image.LANCZOS), dtype=np.float32)
    x = x / max(x.max(), 1e-6)
    mean, std = np.array([0.485, 0.456, 0.406]), np.array([0.229, 0.224, 0.225])
    x = ((x - mean) / std).transpose(2, 0, 1)[None].astype(np.float32)
    out = sess.run(None, {sess.get_inputs()[0].name: x})[0][0, 0]
    out = (out - out.min()) / max(out.max() - out.min(), 1e-6)
    m = Image.fromarray((out * 255).astype(np.uint8)).resize(img.size, Image.LANCZOS)
    # Bordes más limpios: contraste en la transición y un leve suavizado.
    m = m.point(lambda v: 0 if v < 60 else 255 if v > 235 else int((v - 60) * 255 / 175))
    # Encoge el borde ~2 px para no arrastrar el halo del fondo original.
    m = m.filter(ImageFilter.MinFilter(5))
    return m.filter(ImageFilter.GaussianBlur(0.8))


def main(src: str, dst: str) -> None:
    img = Image.open(src).convert("RGB")
    m = mask_for(img)
    out = img.convert("RGBA")
    out.putalpha(m)
    bbox = m.point(lambda v: 255 if v > 20 else 0).getbbox()
    out.crop(bbox).save(dst)
    print(f"OK {dst} {bbox}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
