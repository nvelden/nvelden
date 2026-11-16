"""Generate the animated mycelium banner for the GitHub profile README.

Port of the chemotactic growth in nielsvandervelden.com's MyceliumGrowth:
branches sprout from a seed, veer toward hidden food dots, and burst when
they reach one. The simulation runs once with a fixed seed and is written
out as an SVG in which every branch draws itself in (CSS stroke-dashoffset),
so it animates inside GitHub's <img> sandbox without JavaScript.

Usage: python3 scripts/make_banner.py  -> assets/banner-light.svg, banner-dark.svg
"""

import math
import random
from pathlib import Path

W, H = 880, 250
SEED = 7
FRAME_S = 0.03            # seconds per simulation frame on playback
MAX_BRANCHES = 70
BRANCH_CHANCE = 0.94
START_RADIUS = 1.7
INITIAL_BRANCHES = 18
MAX_FRAMES = 190          # ~5.7 s of growth
SEED_XY = (W * 0.80, H * 0.45)
BASELINE = H - 22         # x-axis of the mass spectrum

THEMES = {
    "light": dict(bg="#F7F3E9", ink="#1C2620", mute="#72796F",
                  hypha="#3E5838", hypha_op=0.32, spore="#D97706", peak="#1C2620", peak_op=0.15, rule="rgba(28,38,32,0.14)"),
    "dark": dict(bg="#0D110F", ink="#EDE6D3", mute="#C4BFA9",
                 hypha="#9BD17C", hypha_op=0.30, spore="#F4B942", peak="#EDE6D3", peak_op=0.13, rule="rgba(237,230,211,0.12)"),
}


class Branch:
    def __init__(self, x, y, angle, radius, born, rng):
        self.pts = [(x, y)]
        self.x, self.y = x, y
        self.angle = angle
        self.radius = radius
        self.speed = rng.random() * 1.5 + 0.9
        self.life = rng.random() * 260 + 120
        self.born = born
        self.alive = True


def simulate():
    rng = random.Random(SEED)
    food = [(rng.uniform(380, W - 4), rng.uniform(4, H - 4)) for _ in range(38)]
    branches = [Branch(*SEED_XY, (2 * math.pi / INITIAL_BRANCHES) * i + rng.random() * 0.1,
                       START_RADIUS, 0, rng) for i in range(INITIAL_BRANCHES)]
    live = list(branches)
    spores = []  # (x, y, frame)

    for frame in range(1, MAX_FRAMES):
        if not live:
            break
        for b in list(live):
            b.life -= 1
            if b.life <= 0:
                b.alive = False
                live.remove(b)
                continue
            steered = False
            for i, (fx, fy) in enumerate(food):
                dx, dy = fx - b.x, fy - b.y
                dist = math.hypot(dx, dy)
                if dist < 5:
                    n = 8 if len(live) < MAX_BRANCHES else 0
                    for j in range(n):
                        nb = Branch(fx, fy, 2 * math.pi / n * j, START_RADIUS * 0.8, frame, rng)
                        branches.append(nb)
                        live.append(nb)
                    spores.append((fx, fy, frame))
                    food.pop(i)
                    steered = True
                    break
                if dist < 28:
                    da = math.atan2(dy, dx) - b.angle
                    b.angle += math.atan2(math.sin(da), math.cos(da)) * 0.5
                    steered = True
                    break
            if not steered:
                b.angle += (rng.random() - 0.5) * 0.22
            b.x += math.cos(b.angle) * b.speed
            b.y += math.sin(b.angle) * b.speed
            if not (0 <= b.x <= W and 0 <= b.y <= H):
                b.alive = False
                live.remove(b)
                b.pts.append((b.x, b.y))
                continue
            b.pts.append((b.x, b.y))
            if len(live) < MAX_BRANCHES and rng.random() > BRANCH_CHANCE and b.radius > 0.5:
                nb = Branch(b.x, b.y, b.angle + rng.random() * 1.2 - 0.6, b.radius * 0.9, frame, rng)
                branches.append(nb)
                live.append(nb)
    return [b for b in branches if len(b.pts) > 3], spores


def spectrum():
    """Stick spectrum: isotope clusters (peaks 1 Da apart, decaying) plus noise.

    Returns (x, height, width, group); peaks in a group rise and fall together.
    """
    rng = random.Random(11)
    peaks = []
    for g in range(16):
        x0 = rng.uniform(24, W - 60)
        base = rng.uniform(40, 150) if g % 3 else rng.uniform(140, 185)
        for k, rel in enumerate((1, 0.62, 0.27, 0.09)):
            peaks.append((x0 + k * 6.5, base * rel, 2.2, g))
    for _ in range(90):
        peaks.append((rng.uniform(16, W - 16), rng.uniform(2, 14), 1.2, 16 + rng.randrange(6)))
    return peaks


def path_d(pts):
    # Keep every 2nd point: halves file size, invisible at this stroke width.
    keep = pts[::2] + ([pts[-1]] if (len(pts) - 1) % 2 else [])
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in keep)


def render(theme, branches, spores):
    t = THEMES[theme]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
           f'role="img" aria-label="Niels van der Velden: data scientist, R/Shiny developer, mass spectrometry">',
           "<style>",
           ".h{fill:none;stroke-linecap:round;stroke-dasharray:1;stroke-dashoffset:1;"
           "animation:grow linear forwards}",
           "@keyframes grow{to{stroke-dashoffset:0}}",
           ".s{opacity:0;transform-box:fill-box;transform-origin:center;"
           "animation:pop .6s ease-out forwards,glow 3.2s ease-in-out infinite}",
           "@keyframes pop{0%{opacity:0;transform:scale(.2)}60%{opacity:1;transform:scale(1.6)}100%{opacity:.85;transform:scale(1)}}",
           "@keyframes glow{0%,100%{opacity:.85}50%{opacity:.25}}",
           ".p{transform-box:fill-box;transform-origin:50% 100%;transform:scaleY(.04);"
           "animation:ion ease-in-out infinite alternate}",
           "@keyframes ion{0%{transform:scaleY(.04)}35%{transform:scaleY(1)}55%{transform:scaleY(.55)}"
           "75%{transform:scaleY(.9)}100%{transform:scaleY(.2)}}",
           ".t{opacity:0;animation:fade 1.2s ease-out forwards}",
           "@keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}",
           "@media (prefers-reduced-motion:reduce){.h,.s,.t,.p{animation:none;opacity:1;stroke-dashoffset:0;transform:none}}",
           "</style>",
           "<defs>",
           '<linearGradient id="fadeL" x1="0" x2="1"><stop offset="0.30" stop-color="#fff" stop-opacity="0"/>'
           '<stop offset="0.55" stop-color="#fff" stop-opacity="1"/></linearGradient>',
           '<mask id="m"><rect width="100%" height="100%" fill="url(#fadeL)"/></mask>',
           f'<radialGradient id="sp"><stop offset="0" stop-color="{t["spore"]}"/>'
           f'<stop offset="1" stop-color="{t["spore"]}" stop-opacity="0"/></radialGradient>',
           "</defs>",
           f'<rect width="{W}" height="{H}" rx="12" fill="{t["bg"]}"/>',
           f'<g fill="{t["peak"]}" fill-opacity="{t["peak_op"]}">',
           *[f'<rect class="p" x="{x - w / 2:.1f}" y="{BASELINE - h:.1f}" width="{w}" height="{h:.1f}" '
             f'style="animation-duration:{2.6 + (g * 0.37) % 2.4:.2f}s;animation-delay:-{(g * 0.61) % 3:.2f}s"/>'
             for x, h, w, g in spectrum()],
           f'<rect x="16" y="{BASELINE}" width="{W - 32}" height="1" fill-opacity="0.22"/>',
           "</g>",
           f'<g mask="url(#m)" stroke="{t["hypha"]}" stroke-opacity="{t["hypha_op"]}">']
    for b in branches:
        delay = b.born * FRAME_S
        dur = max(0.2, (len(b.pts) - 1) * FRAME_S)
        out.append(f'<path class="h" pathLength="1" stroke-width="{b.radius:.2f}" '
                   f'style="animation-duration:{dur:.2f}s;animation-delay:{delay:.2f}s" d="{path_d(b.pts)}"/>')
    out.append("</g>")
    for i, (x, y, frame) in enumerate(spores):
        d1 = frame * FRAME_S
        d2 = d1 + 0.6 + (i % 5) * 0.45
        out.append(f'<circle class="s" cx="{x:.1f}" cy="{y:.1f}" r="7" fill="url(#sp)" '
                   f'style="animation-delay:{d1:.2f}s,{d2:.2f}s"/>')
        out.append(f'<circle class="s" cx="{x:.1f}" cy="{y:.1f}" r="1.6" fill="{t["spore"]}" '
                   f'style="animation-delay:{d1:.2f}s,{d2:.2f}s"/>')
    serif = "Fraunces, Georgia, 'Times New Roman', serif"
    mono = "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace"
    out += [
        f'<text class="t" x="40" y="72" font-family="{serif}" font-size="40" fill="{t["ink"]}" '
        f'style="animation-delay:.2s">Niels van der Velden</text>',
        f'<text class="t" x="42" y="108" font-family="{serif}" font-size="22" fill="{t["ink"]}" '
        f'style="animation-delay:.8s">Data Scientist</text>',
        f'<text class="t" x="42" y="136" font-family="{mono}" font-size="14" fill="{t["mute"]}" '
        f'style="animation-delay:1.3s">R / Shiny · Python · Mass Spectrometry</text>',
        f'<text class="t" x="42" y="160" font-family="{mono}" font-size="13" fill="{t["spore"]}" '
        f'style="animation-delay:1.8s">mycologist at heart</text>',
        f'<text class="t" x="42" y="196" font-family="{mono}" font-size="12.5" fill="{t["mute"]}" '
        f'style="animation-delay:2.3s">Bermuda · nielsvandervelden.com</text>',
        "</svg>",
    ]
    return "\n".join(out)


def main():
    branches, spores = simulate()
    outdir = Path(__file__).resolve().parent.parent / "assets"
    outdir.mkdir(exist_ok=True)
    for theme in THEMES:
        p = outdir / f"banner-{theme}.svg"
        p.write_text(render(theme, branches, spores))
        print(f"{p.name}: {p.stat().st_size // 1024} KB, {len(branches)} branches, {len(spores)} spores")


if __name__ == "__main__":
    main()
