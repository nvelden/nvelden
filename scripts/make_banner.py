"""Generate the animated banner for the GitHub profile README.

The right half shows an annotated MS/MS spectrum of Glu-fibrinopeptide B
(EGVNDNEEGFFSAR), the classic mass spectrometer calibration standard. The b
and y ion m/z values are computed from monoisotopic residue masses (singly
charged). Relative intensities are illustrative: y ions dominate, as is
typical for a tryptic peptide with a C-terminal arginine.

Peaks sweep in from low to high m/z, then keep fluctuating gently like a live
acquisition. Pure CSS animation, so it works inside GitHub's <img> sandbox.

Usage: python3 scripts/make_banner.py  -> assets/banner-light-v5.svg, banner-dark-v5.svg
Bump VERSION whenever the banner changes: GitHub caches images by URL, so a new
filename (and the matching paths in README.md) is what makes the change show up.
"""

import random
from pathlib import Path

VERSION = "v5"
W, H = 880, 250

PEPTIDE = "EGVNDNEEGFFSAR"
RESIDUE = {
    "G": 57.02146, "A": 71.03711, "S": 87.03203, "P": 97.05276, "V": 99.06841,
    "T": 101.04768, "C": 103.00919, "L": 113.08406, "I": 113.08406, "N": 114.04293,
    "D": 115.02694, "Q": 128.05858, "K": 128.09496, "E": 129.04259, "M": 131.04049,
    "H": 137.05891, "F": 147.06841, "R": 156.10111, "Y": 163.06333, "W": 186.07931,
}
PROTON, WATER = 1.00728, 18.01056

# Illustrative relative intensities (0-100).
Y_INT = {1: 32, 2: 18, 3: 30, 4: 40, 5: 22, 6: 78, 7: 62, 8: 70, 9: 100, 10: 55, 11: 42, 12: 30, 13: 12}
B_INT = {2: 24, 3: 30, 4: 14, 5: 10, 6: 9, 7: 7, 8: 6, 9: 6, 10: 5, 11: 5, 12: 4, 13: 3}

# Spectrum panel (right half; the text block lives at x < 430).
PX0, PX1 = 462, 864          # x range of the m/z axis
MZ0, MZ1 = 100, 1500
PEAK_MAX = 150               # px height of a 100% peak (from the bottom edge)
LADDER_Y = 34                # baseline of the sequence ladder

THEMES = {
    "light": dict(bg="#F7F3E9", ink="#1C2620", mute="#72796F", b="#D97706", y="#3E5838",
                  noise="#72796F", ion_op=0.85, noise_op=0.35),
    "dark": dict(bg="#0D110F", ink="#EDE6D3", mute="#C4BFA9", b="#F4B942", y="#9BD17C",
                 noise="#7C7A6C", ion_op=0.85, noise_op=0.45),
}


def fragments():
    """Return list of dicts: kind ('b'|'y'|'p'|'n'), n, mz, intensity, label."""
    res = [RESIDUE[a] for a in PEPTIDE]
    n = len(res)
    ions = []
    for i in range(1, n):
        b = sum(res[:i]) + PROTON
        y = sum(res[n - i:]) + WATER + PROTON
        if i in B_INT:
            ions.append(dict(kind="b", n=i, mz=b, inten=B_INT[i], label=f"b{i}"))
        if i in Y_INT:
            ions.append(dict(kind="y", n=i, mz=y, inten=Y_INT[i], label=f"y{i}"))
    precursor = (sum(res) + WATER + 2 * PROTON) / 2
    ions.append(dict(kind="p", n=0, mz=precursor, inten=16, label="[M+2H]²⁺"))
    rng = random.Random(5)
    for _ in range(70):
        ions.append(dict(kind="n", n=0, mz=rng.uniform(MZ0 + 10, MZ1 - 10),
                         inten=rng.uniform(1, 7), label=None))
    return ions


def x_of(mz):
    return PX0 + (mz - MZ0) / (MZ1 - MZ0) * (PX1 - PX0)


def render(theme):
    t = THEMES[theme]
    serif = "Fraunces, Georgia, 'Times New Roman', serif"
    mono = "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace"
    ions = fragments()
    color = {"b": t["b"], "y": t["y"], "p": t["mute"], "n": t["noise"]}

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="Niels van der Velden: data scientist, R/Shiny, Python, mass spectrometry. '
        f'Annotated MS/MS spectrum of Glu-fibrinopeptide B showing b and y ions.">',
        "<style>",
        # grow in once (sweep by m/z), then fluctuate forever
        ".p{transform-box:fill-box;transform-origin:50% 100%;transform:scaleY(0);"
        "animation:rise .7s cubic-bezier(.2,.8,.3,1) forwards,live ease-in-out infinite alternate}",
        "@keyframes rise{from{transform:scaleY(0)}to{transform:scaleY(1)}}",
        "@keyframes live{0%{transform:scaleY(1)}40%{transform:scaleY(.78)}70%{transform:scaleY(.93)}"
        "100%{transform:scaleY(.7)}}",
        ".t{opacity:0;animation:fade 1s ease-out forwards}",
        "@keyframes fade{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}",
        "@media (prefers-reduced-motion:reduce){.p,.t{animation:none;opacity:1;transform:none}}",
        "</style>",
        f'<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="12"/></clipPath></defs>',
        f'<rect width="{W}" height="{H}" rx="12" fill="{t["bg"]}"/>',
        f'<g clip-path="url(#c)">',
    ]

    def delay(mz):
        return 0.4 + (mz - MZ0) / (MZ1 - MZ0) * 1.6

    # peaks: noise first so ions draw on top
    rng = random.Random(9)
    for ion in sorted(ions, key=lambda d: d["kind"] != "n"):
        x = x_of(ion["mz"])
        h = ion["inten"] / 100 * PEAK_MAX
        w = 1.2 if ion["kind"] == "n" else 2.2
        op = t["noise_op"] if ion["kind"] == "n" else t["ion_op"]
        d1 = delay(ion["mz"])
        live_dur = rng.uniform(1.8, 3.6)
        d2 = d1 + 0.7 + rng.uniform(0, 1.5)
        out.append(
            f'<rect class="p" x="{x - w / 2:.1f}" y="{H - h:.1f}" width="{w}" height="{h:.1f}" '
            f'fill="{color[ion["kind"]]}" fill-opacity="{op}" '
            f'style="animation-duration:.7s,{live_dur:.2f}s;animation-delay:{d1:.2f}s,{d2:.2f}s"/>')
    out.append("</g>")

    # labels: strongest first; skip any whose box would hit a placed label or a
    # peak (at full height) other than its own
    def top_of(ion):
        return H - ion["inten"] / 100 * PEAK_MAX

    real = [i for i in ions if i["kind"] != "n"]
    boxes, placed = [], []
    for ion in sorted((i for i in ions if i["label"]), key=lambda d: -d["inten"]):
        x, y = x_of(ion["mz"]), top_of(ion) - 4
        half = len(ion["label"]) * 2.9 + 1
        box = (x - half, y - 9, x + half, y + 1)
        hits_label = any(box[0] < b[2] and b[0] < box[2] and box[1] < b[3] and b[1] < box[3] for b in boxes)
        hits_peak = any(o is not ion and box[0] - 1 < x_of(o["mz"]) < box[2] + 1 and top_of(o) < box[3]
                        for o in real)
        if hits_label or hits_peak:
            continue
        boxes.append(box)
        placed.append(ion)
        out.append(
            f'<text class="t" x="{x:.1f}" y="{y:.1f}" text-anchor="middle" '
            f'font-family="{mono}" font-size="9.5" fill="{color[ion["kind"]]}" '
            f'style="animation-delay:{delay(ion["mz"]) + 0.5:.2f}s">{ion["label"]}</text>')

    # sequence ladder with cleavage marks for the labelled b / y ions
    labelled = {(i["kind"], i["n"]) for i in placed}
    step = 22
    lx0 = PX1 - step * (len(PEPTIDE) - 1) - 6
    out.append(f'<g class="t" style="animation-delay:.3s" font-family="{mono}" font-size="13" '
               f'fill="{t["ink"]}" text-anchor="middle">')
    for i, aa in enumerate(PEPTIDE):
        out.append(f'<text x="{lx0 + i * step:.1f}" y="{LADDER_Y}">{aa}</text>')
    out.append("</g>")
    out.append(f'<g class="t" style="animation-delay:1.2s" fill="none" stroke-width="1.4">')
    n = len(PEPTIDE)
    for i in range(1, n):
        cx = lx0 + (i - 0.5) * step
        top, bot = LADDER_Y - 15, LADDER_Y + 5
        if ("y", n - i) in labelled:  # y ion: hook at top pointing right (C-terminal side)
            out.append(f'<path d="M{cx:.1f} {(top + bot) / 2:.1f} V{top} h5" stroke="{t["y"]}"/>')
        if ("b", i) in labelled:      # b ion: hook at bottom pointing left (N-terminal side)
            out.append(f'<path d="M{cx:.1f} {(top + bot) / 2:.1f} V{bot} h-5" stroke="{t["b"]}"/>')
    out.append("</g>")
    out.append(
        f'<text class="t" x="{PX1}" y="{LADDER_Y + 20}" text-anchor="end" font-family="{mono}" '
        f'font-size="9.5" fill="{t["mute"]}" style="animation-delay:1.4s">'
        f'<tspan fill="{t["b"]}">b ions</tspan> · <tspan fill="{t["y"]}">y ions</tspan> · Glu-fibrinopeptide B</text>')

    out += [
        f'<text class="t" x="40" y="88" font-family="{serif}" font-size="40" fill="{t["ink"]}" '
        f'style="animation-delay:.2s">Niels van der Velden</text>',
        f'<text class="t" x="42" y="124" font-family="{serif}" font-size="22" fill="{t["ink"]}" '
        f'style="animation-delay:.8s">Data Scientist</text>',
        f'<text class="t" x="42" y="152" font-family="{mono}" font-size="14" fill="{t["mute"]}" '
        f'style="animation-delay:1.3s">R / Shiny · Python · Mass Spectrometry</text>',
        f'<text class="t" x="42" y="184" font-family="{mono}" font-size="12.5" fill="{t["mute"]}" '
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
    for ion in fragments():
        if ion["kind"] in "byp":
            print(f'  {ion["label"]:>9} {ion["mz"]:8.2f}')


if __name__ == "__main__":
    main()
