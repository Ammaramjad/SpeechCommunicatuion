#!/usr/bin/env python3
"""Publication-style recreation of the optimizer convergence figure.

Two panels:
  (a) IEMOCAP  (b) SAVEE
Algorithms: SSA, BOA, ARO, EHOLF
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MultipleLocator


def _bandpass_noise(rng: np.random.Generator, n: int, slow: int = 9, fast: int = 3) -> np.ndarray:
    """Optimizer-like wiggles: slow drift plus a faster ripple."""
    def smooth(window: int) -> np.ndarray:
        raw = rng.normal(0.0, 1.0, n)
        kernel = np.hanning(window)
        kernel /= kernel.sum()
        return np.convolve(raw, kernel, mode="same")

    return 0.65 * smooth(slow) + 0.35 * smooth(fast)


def logistic_curve(
    n: int,
    start: float,
    end: float,
    midpoint: float,
    steepness: float,
) -> np.ndarray:
    t = np.arange(n, dtype=float)
    return start + (end - start) / (1.0 + np.exp(-steepness * (t - midpoint)))


def build_curve(
    *,
    n: int,
    start: float,
    end: float,
    midpoint: float,
    steepness: float,
    noise_scale: float,
    seed: int,
    plateau_from: int | None = None,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    y = logistic_curve(n, start, end, midpoint, steepness)
    noise = _bandpass_noise(rng, n)
    decay = 1.0 - 0.35 * (np.arange(n) / max(n - 1, 1))
    y = y + noise * noise_scale * decay
    y[0] = start
    if plateau_from is not None:
        y[plateau_from:] = end
        blend = min(5, plateau_from)
        for i, idx in enumerate(range(plateau_from - blend, plateau_from)):
            alpha = (i + 1) / (blend + 1)
            y[idx] = (1 - alpha) * y[idx] + alpha * end
    y[-1] = end
    return y


def add_end_labels(ax: plt.Axes, curves: dict[str, np.ndarray], colors: dict[str, str], order: list[str]) -> None:
    x = 99.2
    for name in order:
        y = curves[name][-1]
        color = colors[name]
        ax.annotate(
            f"{y:.1f}%",
            xy=(x, y),
            xytext=(x, y),
            va="center",
            ha="center",
            fontsize=7.5,
            color="white",
            fontweight="bold",
            zorder=5,
            bbox=dict(
                boxstyle="round,pad=0.18,rounding_size=0.32",
                facecolor=color,
                edgecolor="0.2",
                linewidth=0.55,
                alpha=0.93,
            ),
            annotation_clip=False,
        )


def style_axes(ax: plt.Axes, title: str) -> None:
    ax.set_title(title, fontsize=12, fontweight="bold", pad=8)
    ax.set_xlabel("Iterations", fontsize=11)
    ax.set_ylabel("Accuracy (%)", fontsize=11)
    ax.set_xlim(0, 103.5)
    ax.set_ylim(69, 100.8)
    ax.xaxis.set_major_locator(MultipleLocator(20))
    ax.yaxis.set_major_locator(MultipleLocator(5))
    ax.grid(True, which="major", color="0.85", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("0.35")
        spine.set_linewidth(0.8)


def main() -> None:
    n = 101
    t = np.arange(n)

    colors = {
        "SSA": "#1f77b4",
        "BOA": "#ff7f0e",
        "ARO": "#2ca02c",
        "EHOLF": "#d62728",
    }

    iemocap = {
        "SSA": build_curve(
            n=n, start=70.3, end=92.0, midpoint=30, steepness=0.085,
            noise_scale=1.15, seed=11, plateau_from=72,
        ),
        "BOA": build_curve(
            n=n, start=75.0, end=90.0, midpoint=22, steepness=0.09,
            noise_scale=1.25, seed=22, plateau_from=71,
        ),
        "ARO": build_curve(
            n=n, start=80.3, end=93.2, midpoint=34, steepness=0.065,
            noise_scale=1.05, seed=33, plateau_from=None,
        ),
        "EHOLF": build_curve(
            n=n, start=85.2, end=97.0, midpoint=16, steepness=0.115,
            noise_scale=0.85, seed=44, plateau_from=52,
        ),
    }

    savee = {
        "SSA": build_curve(
            n=n, start=72.2, end=93.2, midpoint=32, steepness=0.08,
            noise_scale=1.20, seed=55, plateau_from=None,
        ),
        "BOA": build_curve(
            n=n, start=78.0, end=92.0, midpoint=24, steepness=0.085,
            noise_scale=1.10, seed=66, plateau_from=76,
        ),
        "ARO": build_curve(
            n=n, start=82.0, end=93.8, midpoint=30, steepness=0.065,
            noise_scale=0.95, seed=77, plateau_from=None,
        ),
        "EHOLF": build_curve(
            n=n, start=87.3, end=98.0, midpoint=18, steepness=0.105,
            noise_scale=0.80, seed=88, plateau_from=62,
        ),
    }

    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.15), dpi=160, constrained_layout=True)
    fig.suptitle(
        "Convergence Analysis of Optimization Algorithms",
        fontsize=13.5,
        fontweight="bold",
        y=1.04,
    )

    panels = [
        (axes[0], iemocap, "(a) IEMOCAP Dataset", ["EHOLF", "ARO", "SSA", "BOA"]),
        (axes[1], savee, "(b) SAVEE Dataset", ["EHOLF", "ARO", "BOA"]),
    ]

    for ax, curves, title, label_order in panels:
        style_axes(ax, title)
        for name in ("SSA", "BOA", "ARO", "EHOLF"):
            ax.plot(t, curves[name], color=colors[name], linewidth=1.7, label=name, zorder=3)
        add_end_labels(ax, curves, colors, label_order)
        ax.legend(
            loc="lower right",
            frameon=True,
            fancybox=False,
            edgecolor="0.55",
            fontsize=8.5,
            handlelength=1.6,
            borderpad=0.45,
        )

    out_dir = Path(__file__).resolve().parents[1] / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    png = out_dir / "convergence_analysis.png"
    pdf = out_dir / "convergence_analysis.pdf"
    fig.savefig(png, bbox_inches="tight", facecolor="white")
    fig.savefig(pdf, bbox_inches="tight", facecolor="white")
    print(f"Wrote {png}")
    print(f"Wrote {pdf}")


if __name__ == "__main__":
    main()
