"""Generate the animated banner for the GitHub profile README.

A mass spectrum fills the background: isotope clusters (peaks 1 Da apart,
decaying in height) plus low noise peaks, rising from the bottom edge. Each
cluster rises and falls on its own rhythm. Pure CSS animation, so it works
inside GitHub's <img> sandbox without JavaScript.

Usage: python3 scripts/make_banner.py  -> assets/banner-light-v3.svg, banner-dark-v3.svg
Bump VERSION whenever the banner changes: GitHub caches images by URL, so a new
filename (and the matching paths in README.md) is what makes the change show up.
"""

import random
from pathlib import Path

VERSION = "v3"
W, H = 880, 250

THEMES = {
    "light": dict(bg="#F7F3E9", ink="#1C2620", mute="#72796F", peak="#3E5838", peak_op=0.22),
    "dark": dict(bg="#0D110F", ink="#EDE6D3", mute="#C4BFA9", peak="#9BD17C", peak_op=0.20),
}


def spectrum():
    """Return (x, height, width, group); peaks in a group rise and fall together."""
    rng = random.Random(11)
    peaks = []
    for g in range(18):
        x0 = rng.uniform(20, W - 40)
        base = rng.uniform(50, 160) if g % 3 else rng.uniform(170, 215)
        for k, rel in enumerate((1, 0.62, 0.27, 0.09)):
            peaks.append((x0 + k * 6.5, base * rel, 2.4, g))
    for _ in range(110):
        peaks.append((rng.uniform(4, W - 4), rng.uniform(3, 18), 1.3, 18 + rng.randrange(6)))
    return peaks


def render(theme):
    t = THEMES[theme]
    serif = "Fraunces, Georgia, 'Times New Roman', serif"
    mono = "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace"
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="Niels van der Velden: data scientist, R/Shiny, Python, mass spectrometry">',
        "<style>",
        ".p{transform-box:fill-box;transform-origin:50% 100%;transform:scaleY(.04);"
        "animation:ion ease-in-out infinite alternate}",
        "@keyframes ion{0%{transform:scaleY(.04)}35%{transform:scaleY(1)}55%{transform:scaleY(.55)}"
        "75%{transform:scaleY(.9)}100%{transform:scaleY(.2)}}",
        ".t{opacity:0;animation:fade 1.2s ease-out forwards}",
        "@keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}",
        "@media (prefers-reduced-motion:reduce){.p,.t{animation:none;opacity:1;transform:none}}",
        "</style>",
        f'<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="12"/></clipPath></defs>',
        f'<rect width="{W}" height="{H}" rx="12" fill="{t["bg"]}"/>',
        f'<g clip-path="url(#c)" fill="{t["peak"]}" fill-opacity="{t["peak_op"]}">',
    ]
    for x, h, w, g in spectrum():
        dur = 2.6 + (g * 0.37) % 2.4
        delay = (g * 0.61) % 3
        out.append(f'<rect class="p" x="{x - w / 2:.1f}" y="{H - h:.1f}" width="{w}" height="{h:.1f}" '
                   f'style="animation-duration:{dur:.2f}s;animation-delay:-{delay:.2f}s"/>')
    out += [
        "</g>",
        f'<text class="t" x="40" y="72" font-family="{serif}" font-size="40" fill="{t["ink"]}" '
        f'style="animation-delay:.2s">Niels van der Velden</text>',
        f'<text class="t" x="42" y="108" font-family="{serif}" font-size="22" fill="{t["ink"]}" '
        f'style="animation-delay:.8s">Data Scientist</text>',
        f'<text class="t" x="42" y="136" font-family="{mono}" font-size="14" fill="{t["mute"]}" '
        f'style="animation-delay:1.3s">R / Shiny · Python · Mass Spectrometry</text>',
        f'<text class="t" x="42" y="168" font-family="{mono}" font-size="12.5" fill="{t["mute"]}" '
        f'style="animation-delay:1.8s">Bermuda · nielsvandervelden.com</text>',
        "</svg>",
    ]
    return "\n".join(out)


def main():
    outdir = Path(__file__).resolve().parent.parent / "assets"
    outdir.mkdir(exist_ok=True)
    for theme in THEMES:
        p = outdir / f"banner-{theme}-{VERSION}.svg"
        p.write_text(render(theme))
        print(f"{p.name}: {p.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
