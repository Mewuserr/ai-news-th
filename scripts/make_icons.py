"""Generate simple app icons for the PWA "Add to Home Screen" manifest.

One-off/rerunnable generator - no external assets, just PIL drawing a
space-themed icon: deep navy background, a few star dots, bold "M" (MEW
Station) in the site's purple accent.
"""
import os
import random
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG = (0, 0, 0)           # #000000, site background
ACCENT = (79, 209, 255)  # #4fd1ff, site accent blue
STAR = (255, 255, 255)

SIZES = {
    "icon-192.png": 192,
    "icon-512.png": 512,
    "apple-touch-icon.png": 180,
}


def find_bold_font(size):
    candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def make_icon(size: int, out_path: str):
    img = Image.new("RGB", (size, size), BG)
    draw = ImageDraw.Draw(img)

    rng = random.Random(42)  # deterministic star placement across sizes
    for _ in range(int(size * 0.12)):
        x, y = rng.uniform(0, size), rng.uniform(0, size)
        r = rng.uniform(size * 0.003, size * 0.01)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=STAR)

    font = find_bold_font(int(size * 0.5))
    text = "M"
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - w) / 2 - bbox[0], (size - h) / 2 - bbox[1]), text, fill=ACCENT, font=font)

    img.save(out_path)
    print(f"wrote {out_path}")


def main():
    for filename, size in SIZES.items():
        make_icon(size, os.path.join(ROOT, filename))


if __name__ == "__main__":
    main()
