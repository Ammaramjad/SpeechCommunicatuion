"""Tables 2–17 must be generated from logs, matching the manuscript values."""

from __future__ import annotations

import json
from pathlib import Path

from tables.make_tables import emit

ROOT = Path(__file__).resolve().parents[1]


def test_paper_tables_match_manuscript():
    logs = json.loads((ROOT / "results" / "paper" / "tables.json").read_text())
    tables = emit(logs)

    assert "86.7" in tables["table2_sync"]
    assert "-2.8" in tables["table2_sync"]

    assert "71.4" in tables["table3_pca"]
    assert "12" in tables["table3_pca"]

    assert "Concatenation" in tables["table4_fusion"]
    assert "86.7" in tables["table4_fusion"]

    assert "2 layers, 128 units" in tables["table5_capacity"]

    assert "2.3e-3" in tables["table6_eholf"]
    assert "3.1e-3" in tables["table6_eholf"]

    assert "4.6 h" in tables["table7_compute"]
    assert "101 ms" in tables["table7_compute"]

    assert "Ses01" in tables["table8_folds"]
    assert "86.7 ± 1.3" in tables["table8_folds"]
    assert "92.1 ± 1.3" in tables["table8_folds"]

    assert "ARO (baseline)" in tables["table9_ablation"]
    assert "43" in tables["table9_ablation"]

    assert "85.4±1.4" in tables["table10_baselines"]
    assert "92.1±1.3" in tables["table10_baselines"]

    assert "81.5" in tables["table11_dropout"]

    assert "71.8" in tables["table12_noise"]
    assert "66.2" in tables["table12_noise"]

    assert "58.6" in tables["table13_cross"]
    assert "54.1" in tables["table13_cross"]

    assert "0.312" in tables["table14_shap"]
    assert "38.6" in tables["table15_shap"]
    assert "0.94" in tables["table16_shap"]

    assert "MulT" in tables["table17_matched"]
    assert "MISA" in tables["table17_matched"]
    assert "86.7±1.3" in tables["table17_matched"]


def test_figure_logs_peak_at_reported_accuracy():
    figs = json.loads((ROOT / "results" / "paper" / "figures.json").read_text())
    pop = figs["fig4_population"]
    assert max(pop["iemocap"]["LSTM-EHOLF"]) == 86.7
    assert max(pop["savee"]["LSTM-EHOLF"]) == 92.1
    assert pop["population"][pop["iemocap"]["LSTM-EHOLF"].index(86.7)] == 30
    conv = figs["fig5_convergence"]["iemocap"]["LSTM-EHOLF"]
    assert conv[-1] == 86.7
    cm = figs["fig6_confusion"]["iemocap"]
    total = sum(sum(r) for r in cm)
    assert total == 7344
    correct = sum(cm[i][i] for i in range(4))
    assert abs(100.0 * correct / total - 86.7) < 0.05
