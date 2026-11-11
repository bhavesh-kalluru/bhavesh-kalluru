"""Render the custom profile banner as a GitHub-compatible animated GIF."""
from pathlib import Path
from math import tau, sin, cos
from PIL import Image, ImageDraw
import cairosvg

ROOT = Path(__file__).resolve().parent
svg = ROOT / "hero.svg"
png = ROOT / ".hero-render.png"
cairosvg.svg2png(url=str(svg), write_to=str(png), output_width=1200, output_height=420)
base = Image.open(png).convert("RGBA")
frames = []
for index in range(24):
    angle = tau * index / 24
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    brush = ImageDraw.Draw(overlay, "RGBA")
    for radius, theta, size, rgb in (
        (142, angle, 5, (88, 231, 255)),
        (115, -angle * 1.25, 4, (189, 153, 255)),
        (125, angle * .7 + 1.5, 3, (94, 177, 255)),
    ):
        x = 957 + sin(theta) * radius
        y = 208 - cos(theta) * radius
        for r, alpha in ((16, 14), (10, 34), (6, 70), (size, 255)):
            brush.ellipse((x-r, y-r, x+r, y+r), fill=(*rgb, alpha))
    y = 57 + (index / 24) * 285
    brush.line((805, y, 1120, y), fill=(111, 213, 255, 28), width=2)
    frames.append(Image.alpha_composite(base, overlay).convert("RGB").quantize(colors=160, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
output = ROOT / "hero.gif"
frames[0].save(output, save_all=True, append_images=frames[1:], duration=120, loop=0, optimize=True, disposal=2)
png.unlink(missing_ok=True)
print("Animated banner saved:", output, output.stat().st_size, "bytes")
