"""Generate simple app icons for the PWA "Add to Home Screen" manifest.

One-off/rerunnable generator - no external assets, just PIL drawing a flat
accent-color square with "AI" text, matching the site's existing orange accent.
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCENT = (224, 145, 47)  # #e0912f, same as site's major-news accent
TEXT_COLOR = (26, 19, 0)  # #1a1300, same dark ink used on the accent badge

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
    img = Image.new("RGB", (size, size), ACCENT)
    draw = ImageDraw.Draw(img)
    font = find_bold_font(int(size * 0.42))
    text = "AI"
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - w) / 2 - bbox[0], (size - h) / 2 - bbox[1]), text, fill=TEXT_COLOR, font=font)
    img.save(out_path)
    print(f"wrote {out_path}")


def main():
    for filename, size in SIZES.items():
        make_icon(size, os.path.join(ROOT, filename))


if __name__ == "__main__":
    main()
