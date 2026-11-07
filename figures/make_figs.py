#!/usr/bin/env python3
"""English figures for the results tables. Usage: python make_figs.py   (needs matplotlib)
After drawing, every text artist's full rendered extent is tested against every other one; the script fails if two overlap."""
import itertools
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = os.path.dirname(os.path.abspath(__file__))
SURF, INK, INK2, GRID, MUTE = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df", "#a9a8a2"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
plt.rcParams.update({"font.family": "DejaVu Sans", "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                     "text.color": INK, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2})


def clean(ax):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(MUTE)
    ax.tick_params(length=0)


def check_overlap(fig, name):
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    items = []
    for t in fig.findobj(matplotlib.text.Text):
        if t.get_visible() and t.get_text().strip():
            items.append((t.get_text().replace("\n", " ")[:40], t.get_window_extent(r)))
    bad = [(a, b) for (a, ba), (b, bb) in itertools.combinations(items, 2) if ba.overlaps(bb)]
    if bad:
        print(f"OVERLAP in {name}:", bad[:5])
        sys.exit(1)
    print(f"{name}: {len(items)} text items, no overlap")


def panels(fname, title, cats, colors, specs, figsize, rot=0):
    n = len(specs)
    fig, axs = plt.subplots(1, n, figsize=figsize)
    for ax, (t, vals, fmt, ymax) in zip(axs, specs):
        ax.bar(range(len(vals)), vals, color=colors, width=0.62, edgecolor=SURF, linewidth=2)
        for i, v in enumerate(vals):
            ax.text(i, v + ymax * 0.015, fmt.format(v), ha="center", va="bottom", fontsize=10)
        ax.set_title(t, fontsize=10.5, loc="left")
        ax.set_xticks(range(len(vals)))
        ax.set_xticklabels(cats, fontsize=9, rotation=rot)
        ax.set_ylim(0, ymax)
        ax.yaxis.grid(True, color=GRID, lw=0.8)
        ax.set_axisbelow(True)
        clean(ax)
    fig.suptitle(title, fontsize=11.5, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    check_overlap(fig, fname)
    fig.savefig(f"{OUT}/{fname}", dpi=160)
    plt.close(fig)


# 1. four configurations (Strata 0.2.10). Split = all-cards split engine; ROWS=8 = FNX_PF_STAGE_ROWS=8; Layer split = 2 cards
panels("speed_4_configs.png", "Same PC, 200 ShareGPT requests one at a time, context 8K, MTP, thinking off (Strata 0.2.10)",
       ["Split\ndefault", "Split\nROWS=8", "Layer\nsplit", "1 card"], [MUTE, BLUE, ORANGE, AQUA],
       [("Generated tokens / wall time (tok/s)\nhigher is better", [23.29, 35.70, 40.56, 32.27], "{:.1f}", 50),
        ("Decode median per request (tok/s)\nhigher is better", [57.5, 58.2, 48.65, 36.25], "{:.1f}", 70),
        ("Prompt read median (s)\nlower is better", [4.98, 2.49, 1.05, 1.01], "{:.2f}", 6)], (13, 4.8))

# 2. 0.2.10 vs 0.2.11
panels("split_0.2.10_vs_0.2.11.png", "Split engine, Strata 0.2.10 vs 0.2.11 (same settings, one run each)",
       ["0.2.10", "0.2.11"], [BLUE, ORANGE],
       [("Output tok/s, short\n(generated / wall)\nhigher is better", [35.70, 37.25], "{:.2f}", 46),
        ("Output tok/s, long\n(max_tokens 1024)\nhigher is better", [49.44, 51.12], "{:.2f}", 64),
        ("Decode median tok/s,\nshort\nhigher is better", [58.2, 59.9], "{:.1f}", 74),
        ("Prompt read median s,\nshort\nlower is better", [2.49, 2.39], "{:.2f}", 3.1),
        ("JamC-QA accuracy %\n\nhigher is better", [64.96, 64.79], "{:.2f}", 81)], (17, 4.6))

# 3. FNX_PF_STAGE_ROWS
fig, ax = plt.subplots(figsize=(8.6, 4.8))
lens = ["48 tokens", "200", "780", "3.4K"]
d0 = [2.645, 3.725, 6.087, 4.184]
d8 = [1.948, 2.015, 2.396, 4.215]
w = 0.36
b0 = ax.bar([i - w / 2 for i in range(4)], d0, w, color=MUTE, edgecolor=SURF, linewidth=2, label="default (2048)")
b8 = ax.bar([i + w / 2 for i in range(4)], d8, w, color=BLUE, edgecolor=SURF, linewidth=2, label="FNX_PF_STAGE_ROWS=8")
for bars in (b0, b8):
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.08, f"{b.get_height():.2f}", ha="center", va="bottom", fontsize=9.5)
ax.set_xticks(range(4)); ax.set_xticklabels(lens)
ax.set_ylim(0, 7.6); ax.set_ylabel("Prompt read time (s), median of 3")
ax.yaxis.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True); clean(ax)
ax.legend(frameon=False, loc="upper right", fontsize=10, bbox_to_anchor=(1.0, 1.02))
ax.set_title("Prompt read time by prompt length, Strata 0.2.11, 2x16 GB\n(~70% of routed experts in RAM; lower is better)", fontsize=11, loc="left")
fig.tight_layout()
check_overlap(fig, "stage_rows.png")
fig.savefig(f"{OUT}/stage_rows.png", dpi=160)
