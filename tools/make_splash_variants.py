r"""Make a modlist's splash art at every common screen shape, for MO2 Splash Fit.

One master picture in, a "splash" folder of splash-<shape>.png out (16x9, 16x10, 21x9, 32x9, 4x3, 5x4, 3x2). Put that
folder beside your instance's splash.png; MO2 Splash Fit then gives every player the shape closest to their screen.

Three ways to stretch a master to another shape (--mode):

  frame  (default) for a picture with a border and centred lettering - the Njordlinger demo was made this way. The four
         corners (--corner px square) are kept exactly as they are, the straight edges between them are stretched
         along their length, the middle is filled with --background, and the lettering (--text-box) is cut out and
         re-centred at its original size. Nothing is redrawn, so every shape looks the same apart from its proportions.
  cover  for a full-bleed picture (a landscape, a screenshot): scaled to cover each shape and centre-cropped.
  pad    for anything else: fitted inside each shape and padded with --background.

Needs Python 3 and Pillow (pip install pillow). Examples:

  python make_splash_variants.py my-splash.png
  python make_splash_variants.py my-splash.png --corner 170 --text-box 238 501 1900 697 --out "<your list's MO2 folder>\splash"
  python make_splash_variants.py screenshot.png --mode cover --height 1440

A preview.png contact sheet of every shape is written beside the script's output folder (not inside it, so MO2 Splash
Fit never mistakes it for a splash).
"""
import argparse
import os
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is needed: pip install pillow")

SHAPES = {                        # name: aspect (width / height)
    "16x9": 16 / 9,               # 1920x1080, 2560x1440, 3840x2160
    "16x10": 16 / 10,             # 1920x1200, 2560x1600
    "21x9": 64 / 27,              # 2560x1080, 3440x1440, 5120x2160 ultrawides
    "32x9": 32 / 9,               # 5120x1440 super-ultrawides
    "4x3": 4 / 3,
    "5x4": 5 / 4,
    "3x2": 3 / 2,                 # many laptops and tablets
}


def parse_color(text):
    t = text.lstrip("#")
    if len(t) != 6:
        raise argparse.ArgumentTypeError("colour as RRGGBB, e.g. 000000")
    return tuple(int(t[i:i + 2], 16) for i in (0, 2, 4))


def render_frame(master, aspect, th, corner, text_box, pad, background):
    mw, mh = master.size
    s = th / mh
    tw = int(round(th * aspect))
    big = master.resize((int(round(mw * s)), th), Image.LANCZOS)
    bw = big.width
    c = int(round(corner * s))
    out = Image.new("RGB", (tw, th), background)
    if c > 0:
        # straight edges: one column / row from the middle of the master's band, stretched along its length
        top = big.crop((bw // 2, 0, bw // 2 + 1, c)).resize((max(tw - 2 * c, 1), c))
        bottom = big.crop((bw // 2, th - c, bw // 2 + 1, th)).resize((max(tw - 2 * c, 1), c))
        left = big.crop((0, th // 2, c, th // 2 + 1)).resize((c, max(th - 2 * c, 1)))
        right = big.crop((bw - c, th // 2, bw, th // 2 + 1)).resize((c, max(th - 2 * c, 1)))
        out.paste(top, (c, 0))
        out.paste(bottom, (c, th - c))
        out.paste(left, (0, c))
        out.paste(right, (tw - c, c))
        # the four corners, untouched
        out.paste(big.crop((0, 0, c, c)), (0, 0))
        out.paste(big.crop((bw - c, 0, bw, c)), (tw - c, 0))
        out.paste(big.crop((0, th - c, c, th)), (0, th - c))
        out.paste(big.crop((bw - c, th - c, bw, th)), (tw - c, th - c))
    if text_box:
        # the lettering at its master size, unless it would crowd a narrow frame
        l, t, r, b = text_box
        text = master.crop((max(l - pad, 0), max(t - pad, 0), min(r + pad, mw), min(b + pad, mh)))
        k = s
        max_w = (tw - 2 * c) * 0.92
        if text.width * k > max_w:
            k = max_w / text.width
        text = text.resize((int(round(text.width * k)), int(round(text.height * k))), Image.LANCZOS)
        out.paste(text, ((tw - text.width) // 2, (th - text.height) // 2))
    return out


def render_cover(master, aspect, th):
    tw = int(round(th * aspect))
    k = max(tw / master.width, th / master.height)
    big = master.resize((int(round(master.width * k)), int(round(master.height * k))), Image.LANCZOS)
    x, y = (big.width - tw) // 2, (big.height - th) // 2
    return big.crop((x, y, x + tw, y + th))


def render_pad(master, aspect, th, background):
    tw = int(round(th * aspect))
    k = min(tw / master.width, th / master.height)
    small = master.resize((int(round(master.width * k)), int(round(master.height * k))), Image.LANCZOS)
    out = Image.new("RGB", (tw, th), background)
    out.paste(small, ((tw - small.width) // 2, (th - small.height) // 2))
    return out


def main():
    ap = argparse.ArgumentParser(description="Make splash-<shape>.png variants of a modlist splash for MO2 Splash Fit.")
    ap.add_argument("master", help="the splash picture to start from (any size; PNG or JPG)")
    ap.add_argument("--out", help="output folder (default: a 'splash' folder beside the master)")
    ap.add_argument("--mode", choices=("frame", "cover", "pad"), default="frame")
    ap.add_argument("--corner", type=int, default=0,
                    help="frame mode: size in master pixels of the square corners kept as they are (0 = no border)")
    ap.add_argument("--text-box", type=int, nargs=4, metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"),
                    help="frame mode: the lettering's box in master pixels, re-centred in every shape")
    ap.add_argument("--text-pad", type=int, default=24, help="frame mode: margin taken around the text box (default 24)")
    ap.add_argument("--background", type=parse_color, default=(0, 0, 0), help="fill colour RRGGBB (default 000000)")
    ap.add_argument("--height", type=int, default=2160, help="height of every variant in pixels (default 2160, sharp on 4K)")
    ap.add_argument("--shapes", nargs="+", choices=sorted(SHAPES), default=list(SHAPES))
    a = ap.parse_args()

    master = Image.open(a.master).convert("RGB")
    out_dir = a.out or os.path.join(os.path.dirname(os.path.abspath(a.master)), "splash")
    os.makedirs(out_dir, exist_ok=True)
    if a.mode == "frame" and not a.corner and not a.text_box:
        print("note: frame mode with no --corner and no --text-box gives plain --background pictures; "
              "use --mode cover or pad for a full picture")

    made = []
    for name in a.shapes:
        aspect = SHAPES[name]
        if a.mode == "frame":
            img = render_frame(master, aspect, a.height, a.corner, a.text_box, a.text_pad, a.background)
        elif a.mode == "cover":
            img = render_cover(master, aspect, a.height)
        else:
            img = render_pad(master, aspect, a.height, a.background)
        p = os.path.join(out_dir, f"splash-{name}.png")
        img.save(p, optimize=True)
        print(f"{p}  {img.width}x{img.height}  {os.path.getsize(p):,} bytes")
        made.append(img)

    ph = 240
    tiles = [im.resize((int(im.width * ph / im.height), ph), Image.LANCZOS) for im in made]
    sheet = Image.new("RGB", (max(t.width for t in tiles) + 40, (ph + 30) * len(tiles) + 20), (60, 60, 60))
    y = 20
    for t in tiles:
        sheet.paste(t, (20, y))
        y += ph + 30
    preview = os.path.join(os.path.dirname(os.path.normpath(out_dir)), "splash-preview.png")
    sheet.save(preview)
    print(f"{preview}  (contact sheet - not a splash)")


if __name__ == "__main__":
    main()
