"""Maakt alle logo's/iconen/installerplaatjes uit het origineel (assets/source/logo-original.jpg).
Gebruik:  python tools/make_images.py     (vereist: pip install pillow)"""
import os
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "assets")
src = Image.open(os.path.join(A, "source", "logo-original.jpg")).convert("RGB")

# Logo's
src.save(os.path.join(A, "logo.png"))
src.resize((512, 512), Image.LANCZOS).save(os.path.join(A, "logo_512.png"))

# Favicon / app-icoon: vierkante crop rond de SS, meerdere formaten in één .ico
crop = src.crop((180, 180, 844, 844))
crop.resize((256, 256), Image.LANCZOS).save(
    os.path.join(A, "favicon.ico"), sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
crop.resize((180, 180), Image.LANCZOS).save(os.path.join(A, "apple-touch-icon.png"))
crop.resize((32, 32), Image.LANCZOS).save(os.path.join(A, "favicon-32.png"))

# Installer: zijbalk (2 DPI-formaten) en klein kopplaatje (3 formaten)
tile = src.crop((105, 105, 920, 920))


def sidebar(w, h):
    bg = src.crop((0, 0, 60, 1024)).resize((w, h), Image.BILINEAR).filter(ImageFilter.GaussianBlur(8))
    ov = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(ov)
    for y in range(h):
        k = int(10 + 20 * (1 - y / h))
        d.line([(0, y), (w, y)], fill=(2, k // 2 + 6, k + 14))
    bg = Image.blend(bg, ov, 0.75)
    m = int(w * 0.9)
    bg.paste(tile.resize((m, m), Image.LANCZOS), ((w - m) // 2, int(h * 0.12)))
    return bg


sidebar(164, 314).save(os.path.join(A, "wizard_164x314.bmp"))
sidebar(246, 459).save(os.path.join(A, "wizard_246x459.bmp"))
for s in (55, 83, 110):
    tile.resize((s, s), Image.LANCZOS).save(os.path.join(A, f"wizard_small_{s}.bmp"))
print("klaar")
