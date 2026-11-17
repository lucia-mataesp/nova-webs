"""Genera la cover de un evento Nova Connect (propuesta A · Glow oscuro, 656 x 369).

Uso:
    python crear_cover.py --foto speaker.jpg --logo logo.png --nombre "Ana López" --cargo "Head of Strategy at X" [--slug ana-lopez] [--v a]

Pasos: quita el fondo a la foto, pasa el logo a blanco (y negro), y hace la captura con Chrome.
Salida (fuera de git): visuals/event-covers/salidas/<slug>/cover.png (1312 x 738, 2x) + recursos.
"""
import argparse
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlencode

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from quitar_fondo import main as quitar_fondo  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
COVERS = ROOT / "visuals" / "event-covers"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")


def slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def preparar_logo(src: Path, out_dir: Path) -> None:
    im = Image.open(src).convert("RGBA")
    a = im.getchannel("A")
    if a.getextrema()[0] == 255:  # sin transparencia: logo oscuro sobre fondo claro
        a = im.convert("L").point(lambda v: 255 - v)
        a = a.point(lambda v: 0 if v < 30 else min(255, int(v * 1.15)))
    bbox = a.point(lambda v: 255 if v > 40 else 0).getbbox()
    a = a.crop(bbox)
    for name, col in [("logo_blanco.png", (255, 255, 255)), ("logo_negro.png", (0, 0, 0))]:
        o = Image.new("RGBA", a.size, col + (0,))
        o.putalpha(a)
        o.save(out_dir / name)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--foto", required=True)
    p.add_argument("--logo", required=True)
    p.add_argument("--nombre", required=True)
    p.add_argument("--cargo", required=True)
    p.add_argument("--slug")
    p.add_argument("--v", default="a")
    args = p.parse_args()

    slug = args.slug or slugify(args.nombre)
    out = COVERS / "salidas" / slug
    out.mkdir(parents=True, exist_ok=True)

    quitar_fondo(args.foto, str(out / "speaker.png"))
    preparar_logo(Path(args.logo), out)

    rel = f"salidas/{slug}/"
    q = urlencode({"v": args.v, "photo": rel + "speaker.png", "logo": rel + "logo_blanco.png",
                   "logoDark": rel + "logo_negro.png", "name": args.nombre, "role": args.cargo})
    url = (COVERS / "cover.html").as_uri() + "?" + q
    png = out / "cover.png"
    subprocess.run([str(CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--window-size=656,369", "--force-device-scale-factor=2",
                    "--virtual-time-budget=5000", f"--screenshot={png}", url],
                   check=True, capture_output=True)
    print(f"OK {png}")


if __name__ == "__main__":
    main()
