#!/usr/bin/env python3
"""Regenerate every manuscript table from experiment logs (never hand-edit numbers here)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[1]


def _fmt(v: Optional[float], digits: int = 1) -> str:
    if v is None:
        return "--"
    if isinstance(v, float) and abs(v - round(v, digits)) < 1e-9:
        return f"{v:.{digits}f}"
    return str(v)


def md_table(headers: List[str], rows: List[List[str]]) -> str:
    line = "| " + " | ".join(headers) + " |"
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    body = "\n".join("| " + " | ".join(r) + " |" for r in rows)
    return "\n".join([line, sep, body])


def emit(logs: Dict[str, Any]) -> Dict[str, str]:
    out: Dict[str, str] = {}

    t2 = logs["table2_sync_sensitivity"]
    out["table2_sync"] = md_table(
        ["Condition", "Acc. (%)", "Δ vs aligned"],
        [
            [r["condition"], _fmt(r["acc"]), "--" if r["delta"] is None else _fmt(r["delta"])]
            for r in t2["rows"]
        ],
    )

    t3 = logs["table3_pca_ablation"]
    out["table3_pca"] = md_table(
        ["K", "Retained var. (%)", "Text-only", "A+V+T"],
        [[str(r["K"]), _fmt(r["retained_var"]), _fmt(r["text_only"]), _fmt(r["avt"])] for r in t3["rows"]],
    )

    t4 = logs["table4_fusion_ablation"]
    out["table4_fusion"] = md_table(
        ["Fusion operator", "WA (%)", "Params", "Train time (rel.)"],
        [
            [r["operator"], f"{r['wa']:.1f}±{r['sd']:.1f}", f"{r['params_k']:,}k", f"{r['train_time_rel']:.2f}"]
            for r in t4["rows"]
        ],
    )

    t5 = logs["table5_capacity_ablation"]
    out["table5_capacity"] = md_table(
        ["Configuration", "Train Acc.", "Val. Acc.", "Test Acc.", "Params"],
        [
            [r["configuration"], _fmt(r["train_acc"]), _fmt(r["val_acc"]), _fmt(r["test_acc"]), str(r["params"])]
            for r in t5["rows"]
        ],
    )

    t6 = logs["table6_eholf_hparams"]
    keys = [
        ("lr", "Initial learning rate θ1"),
        ("l2", "L2 factor θ2"),
        ("dropout", "Dropout rate θ3"),
        ("hidden", "LSTM hidden units θ4"),
        ("layers", "LSTM layers (fixed)"),
        ("batch_size", "Batch size (fixed)"),
        ("max_epochs", "Max. epochs / patience"),
        ("optimizer", "Optimizer / LR schedule"),
        ("population", "EHOLF population N / Tmax"),
        ("levy_beta", "Lévy β; AW"),
        ("pca_k", "PCA components K"),
        ("seeds", "Random seeds"),
    ]
    rows = []
    for k, label in keys:
        ie = t6["iemocap"].get(k, t6["iemocap"].get("aw"))
        sa = t6["savee"].get(k, t6["savee"].get("aw"))
        if k == "max_epochs":
            ie = f"{t6['iemocap']['max_epochs']} / {t6['iemocap']['patience']}"
            sa = f"{t6['savee']['max_epochs']} / {t6['savee']['patience']}"
        if k == "population":
            ie = f"{t6['iemocap']['population']} / {t6['iemocap']['t_max']}"
            sa = f"{t6['savee']['population']} / {t6['savee']['t_max']}"
        if k == "levy_beta":
            ie = f"{t6['iemocap']['levy_beta']}; {t6['iemocap']['aw']}"
            sa = f"{t6['savee']['levy_beta']}; {t6['savee']['aw']}"
        rows.append([label, str(ie), str(sa)])
    out["table6_eholf"] = md_table(["Hyperparameter", "IEMOCAP", "SAVEE"], rows)

    t7 = logs["table7_compute_cost"]
    out["table7_compute"] = md_table(
        ["Phase", "Per utterance", "IEMOCAP total", "SAVEE total", "Pipeline share (%)"],
        [
            [r["phase"], r["per_utt"], r["iemocap"], r["savee"], "--" if r["share"] is None else str(r["share"])]
            for r in t7["rows"]
        ],
    )

    t8 = logs["table8_fold_results"]

    def fold_rows(items, mean):
        rows = [
            [r["fold"], _fmt(r["wa"]), _fmt(r["ua"]), _fmt(r["macro_f1"]), _fmt(r["precision"]), f"{r['auc']:.2f}"]
            for r in items
        ]
        rows.append(
            [
                "Mean ± SD",
                f"{mean['wa']:.1f} ± {mean['wa_sd']:.1f}",
                f"{mean['ua']:.1f} ± {mean['ua_sd']:.1f}",
                f"{mean['macro_f1']:.1f} ± {mean['f1_sd']:.1f}",
                f"{mean['precision']:.1f} ± {mean['prec_sd']:.1f}",
                f"{mean['auc']:.2f} ± {mean['auc_sd']:.2f}",
            ]
        )
        return rows

    out["table8_folds"] = (
        "### IEMOCAP\n"
        + md_table(["Fold", "WA", "UA", "Macro-F1", "Precision", "AUC (micro)"], fold_rows(t8["iemocap"], t8["iemocap_mean"]))
        + "\n\n### SAVEE\n"
        + md_table(["Fold", "WA", "UA", "Macro-F1", "Precision", "AUC (micro)"], fold_rows(t8["savee"], t8["savee_mean"]))
    )

    t9 = logs["table9_eholf_ablation"]
    out["table9_ablation"] = md_table(
        ["Variant", "Accuracy (%)", "Convergence iterations"],
        [[r["variant"], _fmt(r["accuracy"]), str(r["convergence_iterations"])] for r in t9["rows"]],
    )

    t10 = logs["table10_baselines"]
    methods = ["RNN", "GRU", "GAN", "TNN", "LSTM-EHOLF"]

    def blk(ds):
        d = t10[ds]
        rows = []
        for metric, key, sdkey in [
            ("Accuracy (%)", "wa", "wa_sd"),
            ("UA (%)", "ua", "ua_sd"),
            ("F1 Score (%)", "f1", "f1_sd"),
            ("Precision (%)", "prec", "prec_sd"),
        ]:
            rows.append([metric] + [f"{d[m][key]:.1f}±{d[m][sdkey]:.1f}" for m in methods])
        return md_table(["Metric"] + methods, rows)

    out["table10_baselines"] = "### IEMOCAP\n" + blk("iemocap") + "\n\n### SAVEE\n" + blk("savee")

    t11 = logs["table11_dropout"]
    out["table11_dropout"] = md_table(
        ["Configuration", "IEMOCAP (%)", "SAVEE (%)"],
        [[r["configuration"], _fmt(r["iemocap"]), _fmt(r["savee"])] for r in t11["rows"]],
    )

    t12 = logs["table12_noise"]
    out["table12_noise"] = md_table(
        ["Degradation", "IEMOCAP", "SAVEE", "TNN IEMOCAP", "TNN SAVEE"],
        [
            [r["condition"], _fmt(r["iemocap"]), _fmt(r["savee"]), _fmt(r["tnn_iemocap"]), _fmt(r["tnn_savee"])]
            for r in t12["rows"]
        ],
    )

    t13 = logs["table13_cross_dataset"]
    out["table13_cross"] = md_table(
        ["Train → Test", "Setting", "Accuracy (%)"],
        [[r["setting"], r["kind"], _fmt(r["acc"])] for r in t13["rows"]],
    )

    t14 = logs["table14_shap_features"]
    out["table14_shap"] = md_table(
        ["Feature category", "Specific features", "Mean SHAP", "Dominant emotion(s)", "Interpretation"],
        [
            [r["category"], r["features"], f"{r['mean_shap']:.3f}", r["dominant"], r["interpretation"]]
            for r in t14["rows"]
        ],
    )

    t15 = logs["table15_shap_modality"]
    out["table15_shap"] = md_table(
        ["Emotion", "Audio (%)", "Visual (%)", "Textual (%)"],
        [[r["emotion"], _fmt(r["audio"]), _fmt(r["visual"]), _fmt(r["textual"])] for r in t15["rows"]],
    )

    t16 = logs["table16_shap_stability"]
    out["table16_shap"] = md_table(
        ["Source of variation", "SD audio", "SD visual", "SD text", "Max. SD (class)", "ρ", "Dominant preserved (%)"],
        [
            [r["source"], _fmt(r["sd_audio"]), _fmt(r["sd_visual"]), _fmt(r["sd_text"]), r["max_sd"], f"{r['rho']:.2f}", str(r["dominant_preserved"])]
            for r in t16["rows"]
        ],
    )

    t17 = logs["table17_matched_sota"]

    def sota(rows):
        return md_table(
            ["Method", "Mod.", "Cls.", "Protocol", "Acc./WA (%)", "UA (%)"],
            [
                [
                    r["method"],
                    r["mod"],
                    str(r["cls"]),
                    r["protocol"],
                    f"{r['wa']:.1f}±{r['wa_sd']:.1f}",
                    f"{r['ua']:.1f}±{r['ua_sd']:.1f}",
                ]
                for r in rows
            ],
        )

    out["table17_matched"] = "### IEMOCAP\n" + sota(t17["iemocap"]) + "\n\n### SAVEE\n" + sota(t17["savee"])
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, default=ROOT / "results" / "paper" / "tables.json")
    p.add_argument("--out", type=Path, default=ROOT / "tables" / "generated")
    args = p.parse_args()
    logs = json.loads(Path(args.source).read_text())
    tables = emit(logs)
    args.out.mkdir(parents=True, exist_ok=True)
    index = ["# Regenerated manuscript tables", "", f"Source: `{args.source}`", ""]
    for name, md in tables.items():
        (args.out / f"{name}.md").write_text(md + "\n")
        index.append(f"## {name}\n\n{md}\n")
    (args.out / "ALL_TABLES.md").write_text("\n".join(index) + "\n")
    print(f"Wrote {len(tables)} tables to {args.out}")


if __name__ == "__main__":
    main()
