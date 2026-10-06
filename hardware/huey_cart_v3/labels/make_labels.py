#!/usr/bin/env python3
"""Huey's Station cart labels -> print-ready PDF (Letter, 300 dpi, true scale).

Card art:  put images in ./art/  (any size; they are cropped to fill 64 x 26 mm).
Names:     one per line in names.txt, or taken from the art file names.

    python make_labels.py              -> labels.pdf
    python make_labels.py --blank      -> blank cut template

Print at 100% / "Actual size" (not "Fit to page"). Cut on the solid lines.
Card: 64 x 26 mm (slides into the cart window). Name strip: 59 x 5.8 mm (top of the cap).
"""
import sys, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

DPI = 300
mm = lambda v: round(v / 25.4 * DPI)
PAGE = (mm(215.9), mm(279.4))
CARD = (64, 26); NAME = (59, 5.8); MARGIN = 12; GAP = 4
HERE = Path(__file__).parent

def font(size_mm, bold=True):
    for f in ["DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", "arialbd.ttf" if bold else "arial.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
        try: return ImageFont.truetype(f, mm(size_mm))
        except OSError: pass
    return ImageFont.load_default()

def fit_text(draw, text, box_w, box_h, start=4.0):
    s = start
    while s > 1.2:
        f = font(s); w = draw.textlength(text, font=f)
        if w <= box_w and mm(s) <= box_h: return f
        s -= 0.1
    return font(1.2)

def card_img(path):
    im = Image.open(path).convert("RGB")
    return ImageOps.fit(im, (mm(CARD[0]), mm(CARD[1])), Image.LANCZOS)

def outline(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], outline=(120, 120, 120), width=2)

def build(blank=False):
    arts = sorted(p for p in (HERE / "art").glob("*") if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")) if not blank else []
    names_file = HERE / "names.txt"
    names = [l.strip() for l in names_file.read_text().splitlines() if l.strip()] if names_file.exists() and not blank else []
    if not names and arts: names = [re.sub(r"[_-]+", " ", p.stem) for p in arts]
    cw, ch = mm(CARD[0]), mm(CARD[1]); nw, nh = mm(NAME[0]), mm(NAME[1]); g = mm(GAP); m = mm(MARGIN)
    cols = (PAGE[0] - 2*m + g) // (cw + g)
    pages, page, d = [], None, None
    def new_page():
        p = Image.new("RGB", PAGE, "white"); dd = ImageDraw.Draw(p)
        dd.text((m, mm(4)), "Huey's Station cart labels - print at 100% (Actual size). Cards 64x26 mm, names 59x5.8 mm.", fill=(90,90,90), font=font(2.6, False))
        return p, dd
    page, d = new_page(); y = m
    # cards
    n_cards = len(arts) if arts else cols * 5
    i = 0
    while i < n_cards:
        if y + ch > PAGE[1] - m: pages.append(page); page, d = new_page(); y = m
        for c in range(cols):
            if i >= n_cards: break
            x = m + c * (cw + g)
            if arts: page.paste(card_img(arts[i]), (x, y))
            outline(d, x, y, cw, ch); i += 1
        y += ch + g
    # name strips
    y += g; n_names = len(names) if names else cols * 10
    ncols = (PAGE[0] - 2*m + g) // (nw + g); i = 0
    while i < n_names:
        if y + nh > PAGE[1] - m: pages.append(page); page, d = new_page(); y = m
        for c in range(ncols):
            if i >= n_names: break
            x = m + c * (nw + g)
            if names:
                t = names[i].upper(); f = fit_text(d, t, nw - mm(3), nh - mm(1.6), 3.4)
                tw = d.textlength(t, font=f); bb = d.textbbox((0, 0), t, font=f)
                d.text((x + (nw - tw)/2, y + (nh - (bb[3]-bb[1]))/2 - bb[1]), t, fill=(30, 25, 20), font=f)
            outline(d, x, y, nw, nh); i += 1
        y += nh + g
    pages.append(page)
    out = HERE / ("labels_blank.pdf" if blank else "labels.pdf")
    pages[0].save(out, save_all=True, append_images=pages[1:], resolution=DPI)
    print(f"wrote {out} ({len(pages)} page{'s' if len(pages) > 1 else ''})")

if __name__ == "__main__":
    build(blank="--blank" in sys.argv)
