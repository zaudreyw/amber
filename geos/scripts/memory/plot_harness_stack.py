#!/usr/bin/env python3
"""Generate plots showing harness-stack progression: A1 → A2 → A3 → M1-u.

Produces:
  misc/memory_artifacts/plots/stack_progression.png — bar + error bars
  misc/memory_artifacts/plots/per_task_heatmap.png — 17 tasks × conditions
  misc/memory_artifacts/plots/variance_decomposition.png — seed-level scatter
  misc/memory_artifacts/plots/cost_vs_quality.png — cost/latency vs fa0
"""
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib>=3.8", "numpy>=1.26", "pandas>=2.0"]
# ///
from __future__ import annotations

import csv
from pathlib import Path
from statistics import mean, stdev

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


REPO = Path("/home/matt/sci/repo3")
CSV = REPO / "misc" / "memory_artifacts" / "plot_data_per_seed.csv"
TASK_CSV = REPO / "misc" / "memory_artifacts" / "plot_data_per_task.csv"
OUT = REPO / "misc" / "memory_artifacts" / "plots"
OUT.mkdir(parents=True, exist_ok=True)


# Canonical progression for the main paper figure
STACK_ORDER = [
    ("A1_noplug",                    "Vanilla CC\n(no plugin)"),
    ("A2_plug_nohook",               "+ RAG"),
    ("A3_plug_hook",                 "+ RAG + SR"),
    ("M1_u_cheatsheet_ungrounded",   "+ RAG + SR + Memory\n(M1-u, hero)"),
]


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV)
    # Filter out contaminated seeds
    df["is_clean"] = df["contaminated"].isna() | (df["contaminated"] == "")
    return df


def plot_stack_progression(df: pd.DataFrame):
    """Bar chart: fa0 mean with stdev error bars across the canonical stack.

    Also overlays individual-seed scatter points so variance is visible.
    """
    fig, (ax_fa, ax_cost) = plt.subplots(1, 2, figsize=(13, 5.5), gridspec_kw={"width_ratios": [1.5, 1]})

    labels = []
    means = []
    stds = []
    seed_points = []  # list of (x_idx, fa0) pairs
    costs = []  # mean per-seed cost
    latencies = []  # mean per-seed elapsed
    tool_calls = []
    for i, (cond, label) in enumerate(STACK_ORDER):
        sub = df[(df["condition"] == cond) & (df["is_clean"])]
        fa0s = sub["fa0_mean_treesim"].tolist()
        if not fa0s:
            means.append(0); stds.append(0); labels.append(label + "\n(no data)")
            costs.append(0); latencies.append(0); tool_calls.append(0)
            continue
        labels.append(f"{label}\n(n={len(fa0s)})")
        means.append(mean(fa0s))
        stds.append(stdev(fa0s) if len(fa0s) > 1 else 0)
        for f in fa0s: seed_points.append((i, f))
        costs.append(mean(sub["total_cost_usd"].tolist()))
        latencies.append(mean(sub["mean_elapsed_sec"].tolist()))
        tool_calls.append(mean(sub["mean_tool_calls"].tolist()))

    x = np.arange(len(labels))
    colors = ["#b4b4b4", "#6495ed", "#4a90e2", "#2c5aa0"]
    bars = ax_fa.bar(x, means, yerr=stds, capsize=5, color=colors, edgecolor="black", alpha=0.85)
    for i, pt_y in seed_points:
        ax_fa.scatter([i], [pt_y], color="red", s=30, zorder=3, alpha=0.7, edgecolor="black", linewidth=0.5)
    ax_fa.set_xticks(x)
    ax_fa.set_xticklabels(labels, fontsize=9)
    ax_fa.set_ylabel("fa0 TreeSim", fontsize=11)
    ax_fa.set_title("Harness stack contribution (17 v2 tasks, minimax-m2.7)\n"
                     "Bars = mean across seeds ± 1 std, red dots = individual seeds",
                     fontsize=11)
    ax_fa.set_ylim(0, 1.0)
    ax_fa.grid(axis="y", alpha=0.3)
    # Annotate deltas
    for i in range(1, len(means)):
        delta = means[i] - means[i-1]
        ax_fa.annotate(f"+{delta:.3f}" if delta >= 0 else f"{delta:.3f}",
                        xy=(i, means[i] + stds[i] + 0.02), ha="center", fontsize=9,
                        color="darkgreen" if delta >= 0.02 else ("red" if delta <= -0.02 else "black"),
                        fontweight="bold")

    # Side panel: cost vs fa0 by condition (showing cost-efficiency)
    ax_cost.scatter(costs, means, s=120, c=colors, edgecolor="black", linewidth=1, zorder=3)
    for i, (cx, cy) in enumerate(zip(costs, means)):
        short_label = STACK_ORDER[i][1].split("\n")[0].replace("+", "").strip()
        ax_cost.annotate(short_label, xy=(cx, cy), xytext=(7, 3),
                          textcoords="offset points", fontsize=8)
    ax_cost.set_xlabel("mean cost per 17-task run (USD)", fontsize=10)
    ax_cost.set_ylabel("fa0 TreeSim", fontsize=10)
    ax_cost.set_title("Cost vs quality", fontsize=11)
    ax_cost.set_ylim(0, 1.0)
    ax_cost.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUT / "stack_progression.png", dpi=140)
    plt.close(fig)
    print(f"wrote {OUT / 'stack_progression.png'}")


def plot_axes_comparison(df: pd.DataFrame):
    """Four-panel plot: fa0, latency, RAG calls, cost vs the canonical stack."""
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))

    metrics = [
        ("fa0_mean_treesim", "fa0 TreeSim", "higher is better"),
        ("mean_elapsed_sec", "mean elapsed per task (sec)", "lower is better"),
        ("mean_tool_calls",  "mean tool calls per task", "lower = more efficient"),
        ("total_cost_usd",   "total cost per 17-task seed (USD)", "lower is better"),
    ]
    colors = ["#b4b4b4", "#6495ed", "#4a90e2", "#2c5aa0"]
    for ax, (col, ylabel, sub) in zip(axes.ravel(), metrics):
        x = np.arange(len(STACK_ORDER))
        y = []; yerr = []; labels = []
        for cond, label in STACK_ORDER:
            dsub = df[(df["condition"] == cond) & (df["is_clean"])]
            vals = dsub[col].tolist()
            if vals:
                y.append(mean(vals))
                yerr.append(stdev(vals) if len(vals) > 1 else 0)
                labels.append(f"{label.split(chr(10))[0]}\nn={len(vals)}")
            else:
                y.append(0); yerr.append(0); labels.append(label.split("\n")[0] + "\n(no data)")
        ax.bar(x, y, yerr=yerr, capsize=4, color=colors, edgecolor="black", alpha=0.85)
        ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_title(f"{ylabel} ({sub})", fontsize=10)
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Harness stack across key axes (minimax-m2.7, 17 v2 tasks)", fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "axes_comparison.png", dpi=140)
    plt.close(fig)
    print(f"wrote {OUT / 'axes_comparison.png'}")


def plot_per_task_heatmap(df_task: pd.DataFrame):
    """17 tasks × conditions heatmap showing per-task fa0 averaged over clean seeds."""
    df = df_task.copy()
    df["is_clean"] = df["contaminated"].isna() | (df["contaminated"] == "")
    df = df[df["is_clean"]]

    conditions = [c for c, _ in STACK_ORDER]
    tasks = sorted(df["task"].dropna().unique().tolist())

    matrix = np.full((len(tasks), len(conditions)), np.nan)
    for ci, cond in enumerate(conditions):
        for ti, task in enumerate(tasks):
            sub = df[(df["condition"] == cond) & (df["task"] == task)]
            vals = sub["treesim"].dropna().tolist()
            if vals:
                matrix[ti, ci] = float(mean(vals))

    fig, ax = plt.subplots(figsize=(8, 9))
    im = ax.imshow(matrix, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(conditions)))
    ax.set_xticklabels([STACK_ORDER[i][1].split("\n")[0] for i in range(len(conditions))],
                        rotation=30, ha="right", fontsize=9)
    ax.set_yticks(range(len(tasks)))
    ax.set_yticklabels([t[:40] for t in tasks], fontsize=8)
    for ti in range(len(tasks)):
        for ci in range(len(conditions)):
            v = matrix[ti, ci]
            if not np.isnan(v):
                ax.text(ci, ti, f"{v:.2f}", ha="center", va="center",
                         color="black" if v > 0.4 else "white", fontsize=8)
    fig.colorbar(im, ax=ax, label="fa0 TreeSim (mean across clean seeds)")
    ax.set_title("Per-task fa0 TreeSim across harness stack\n(green = good; rows = 17 test tasks)",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(OUT / "per_task_heatmap.png", dpi=140)
    plt.close(fig)
    print(f"wrote {OUT / 'per_task_heatmap.png'}")


def plot_seed_variance(df: pd.DataFrame):
    """Strip plot: per-seed fa0 for each condition to show seed variance structure."""
    fig, ax = plt.subplots(figsize=(11, 5.5))
    conditions = [c for c, _ in STACK_ORDER] + ["M_placebo", "M1_g_cheatsheet_grounded", "M4_u_items_ungrounded", "M4_g_items_grounded", "M3_g_tool_grounded"]
    labels = [STACK_ORDER[i][1].split("\n")[0] for i in range(len(STACK_ORDER))] + ["placebo", "M1-g", "M4-u", "M4-g", "M3-g"]

    for i, cond in enumerate(conditions):
        sub = df[df["condition"] == cond]
        clean = sub[(sub["contaminated"].isna()) | (sub["contaminated"] == "")]
        contam = sub[(~sub["contaminated"].isna()) & (sub["contaminated"] != "")]
        clean_fa0 = clean["fa0_mean_treesim"].tolist()
        contam_fa0 = contam["fa0_mean_treesim"].tolist()
        xs = [i + np.random.uniform(-0.12, 0.12) for _ in clean_fa0]
        ax.scatter(xs, clean_fa0, s=70, edgecolor="black", color="#4a90e2", zorder=3, label="clean seed" if i == 0 else "")
        xs2 = [i + np.random.uniform(-0.12, 0.12) for _ in contam_fa0]
        ax.scatter(xs2, contam_fa0, s=70, edgecolor="black", color="red", marker="x", zorder=3, label="API-contaminated" if i == 0 else "")
        if clean_fa0:
            m = mean(clean_fa0)
            ax.hlines(m, i - 0.25, i + 0.25, color="black", lw=2)
            ax.annotate(f"{m:.3f}", xy=(i + 0.28, m), fontsize=9, va="center", fontweight="bold")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_ylabel("fa0 TreeSim (per-seed)", fontsize=11)
    ax.set_ylim(-0.05, 1.05)
    ax.grid(axis="y", alpha=0.3)
    ax.legend(loc="lower right")
    ax.set_title("Per-seed fa0 distribution showing sampling variance and API contamination", fontsize=11)
    fig.tight_layout()
    fig.savefig(OUT / "seed_variance.png", dpi=140)
    plt.close(fig)
    print(f"wrote {OUT / 'seed_variance.png'}")


def main() -> int:
    df = load_data()
    df_task = pd.read_csv(TASK_CSV)
    plot_stack_progression(df)
    plot_axes_comparison(df)
    plot_per_task_heatmap(df_task)
    plot_seed_variance(df)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
