#!/usr/bin/env python3
"""Regenerate Figs. 3–7 from experiment logs (architecture Figs. 1–2 are static drawings)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]


def fig3_eholf_flowchart(out: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.2, 10.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 14)
    ax.axis("off")
    boxes = [
        (3, 12.6, "Initialize population θ ~ U(lb, ub)\nevaluate f(θ)=1−Acc_val"),
        (3, 10.8, "Update AW(t) (Eq. AIW)"),
        (3, 9.0, "rand() < 0.6 ?"),
        (0.4, 7.0, "Lévy exploration\nθ ← θ + s(θ−θk)+s(θ*−θ)"),
        (5.6, 7.0, "AIW exploitation\nθ* + AW(θa−θb)+(1−AW)N(0,σ²)"),
        (3, 5.0, "Clip to bounds, evaluate f"),
        (3, 3.2, "Greedy accept; update θ*"),
        (3, 1.4, "Return θ* after Tmax or stall"),
    ]
    for x, y, text in boxes:
        ax.add_patch(FancyBboxPatch((x, y), 4 if x == 3 else 3.8, 1.4, boxstyle="round,pad=0.05", facecolor="#e8f1ff", edgecolor="#1f4e79"))
        ax.text(x + (2 if x == 3 else 1.9), y + 0.7, text, ha="center", va="center", fontsize=8)
    for y1, y2 in [(12.6, 12.2), (10.8, 10.4)]:
        pass
    ax.annotate("", xy=(5, 12.6), xytext=(5, 12.2))
    ax.plot([5, 5], [12.55, 11.2], color="#1f4e79")
    ax.plot([5, 5], [10.75, 10.4], color="#1f4e79")
    ax.plot([5, 5], [8.95, 8.4], color="#1f4e79")
    ax.plot([5, 2.3], [8.4, 8.4], color="#1f4e79")
    ax.plot([2.3, 2.3], [8.4, 8.4], color="#1f4e79")
    ax.plot([5, 7.5], [8.4, 8.4], color="#1f4e79")
    ax.plot([2.3, 2.3], [8.4, 7.0], color="#1f4e79")
    ax.plot([7.5, 7.5], [8.4, 7.0], color="#1f4e79")
    ax.plot([2.3, 5], [7.0, 6.4], color="#1f4e79")
    ax.plot([7.5, 5], [7.0, 6.4], color="#1f4e79")
    ax.plot([5, 5], [6.4, 6.4], color="#1f4e79")
    ax.plot([5, 5], [4.95, 4.6], color="#1f4e79")
    ax.plot([5, 5], [3.15, 2.8], color="#1f4e79")
    ax.set_title("Fig. 3  EHOLF exploration / exploitation")
    fig.tight_layout()
    fig.savefig(out / "fig3.png", dpi=160)
    plt.close(fig)


def fig4_population(data: dict, out: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    pops = data["population"]
    for ax, split, title in [(axes[0], "iemocap", "IEMOCAP"), (axes[1], "savee", "SAVEE")]:
        for name, ys in data[split].items():
            ax.plot(pops, ys, marker="o", label=name)
        ax.set_xlabel("Population size")
        ax.set_ylabel("Validation accuracy (%)")
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
    fig.suptitle("Fig. 4  Optimizer accuracy vs population size")
    fig.tight_layout()
    fig.savefig(out / "fig4.png", dpi=160)
    plt.close(fig)


def fig5_convergence(data: dict, out: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    it = data["iterations"]
    for ax, split, title in [(axes[0], "iemocap", "IEMOCAP"), (axes[1], "savee", "SAVEE")]:
        for name, ys in data[split].items():
            ax.plot(it, ys, label=name)
        ax.set_xlabel("Iteration")
        ax.set_ylabel("Best validation accuracy (%)")
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
    fig.suptitle("Fig. 5  EHOLF convergence")
    fig.tight_layout()
    fig.savefig(out / "fig5.png", dpi=160)
    plt.close(fig)


def fig6_confusion(data: dict, out: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8))
    for ax, key, labkey, title in [
        (axes[0], "iemocap", "iemocap_labels", "IEMOCAP"),
        (axes[1], "savee", "savee_labels", "SAVEE"),
    ]:
        cm = np.asarray(data[key], dtype=float)
        cmn = cm / cm.sum(axis=1, keepdims=True)
        im = ax.imshow(cmn, cmap="Blues", vmin=0, vmax=1)
        labels = data[labkey]
        ax.set_xticks(range(len(labels)))
        ax.set_yticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
        ax.set_title(title)
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                ax.text(j, i, f"{cmn[i, j]*100:.0f}", ha="center", va="center", fontsize=7)
    fig.suptitle("Fig. 6  Confusion matrices (row-normalized %)")
    fig.tight_layout()
    fig.savefig(out / "fig6.png", dpi=160)
    plt.close(fig)


def fig7_roc(data: dict, out: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.4))
    fpr = data["fpr"]
    for ax, split, title in [(axes[0], "iemocap", "IEMOCAP"), (axes[1], "savee", "SAVEE")]:
        block = data[split]
        for k, ys in block.items():
            if k == "auc":
                continue
            ax.plot(fpr, ys, label=k)
        ax.plot([0, 1], [0, 1], ls="--", c="gray", lw=0.8)
        ax.set_xlabel("False positive rate")
        ax.set_ylabel("True positive rate")
        ax.set_title(title)
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)
    fig.suptitle("Fig. 7  One-vs-rest ROC")
    fig.tight_layout()
    fig.savefig(out / "fig7.png", dpi=160)
    plt.close(fig)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, default=ROOT / "results" / "paper" / "figures.json")
    p.add_argument("--out", type=Path, default=ROOT / "figures" / "generated")
    args = p.parse_args()
    data = json.loads(Path(args.source).read_text())
    args.out.mkdir(parents=True, exist_ok=True)
    fig3_eholf_flowchart(args.out)
    fig4_population(data["fig4_population"], args.out)
    fig5_convergence(data["fig5_convergence"], args.out)
    fig6_confusion(data["fig6_confusion"], args.out)
    fig7_roc(data["fig7_roc"], args.out)
    print(f"Wrote figures to {args.out}")


if __name__ == "__main__":
    main()
