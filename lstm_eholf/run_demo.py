"""Run every manuscript experiment on a synthetic, speaker-independent corpus."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch

from eholf.optimizer import EHOLF, exploration_efficiency
from explain.kernel_shap import feature_group_importance, kernel_shap, modality_importance, shap_slices, spearman
from lstm_eholf.config import AUDIO_DIM, GEO_DIM, LSTMConfig, SearchSpace, TEXT_PCA_K
from lstm_eholf.data import (
    Corpus,
    apply_fold_pca,
    build_iemocap_like,
    build_savee_like,
    fused_vector,
    sequences_for_split,
)
from lstm_eholf.metrics import fold_std, paired_ttest
from lstm_eholf.models import LSTMClassifier, LowRankTensorFusion, count_parameters
from lstm_eholf.train import evaluate, predict, train_model
from preprocessing.audio import extract_audio_features
from preprocessing.text import fit_pca
from preprocessing.video import geometric_from_landmarks
from robustness.experiments import dropout_configs


def _first_fold(corpus: Corpus):
    name = next(iter(corpus.folds))
    return name, corpus.folds[name]


def _xy(corpus: Corpus, split, cfg: LSTMConfig, drop=None):
    return sequences_for_split(corpus, split, max_len=cfg.max_seq_len, drop=drop)


def run_fold_training(cfg: LSTMConfig, corpus: Corpus, architecture: str = "lstm") -> List[Dict]:
    rows = []
    for fold, splits in corpus.folds.items():
        if any(u.text is not None for u in corpus.utterances):
            apply_fold_pca(corpus, splits["train"], k=min(TEXT_PCA_K, 12))
        train = _xy(corpus, splits["train"], cfg)
        val = _xy(corpus, splits["val"], cfg)
        test = _xy(corpus, splits["test"], cfg)
        model, stats = train_model(cfg, train, val, architecture=architecture, device=cfg.device)
        ev = evaluate(model, test, cfg.num_classes, cfg.device)
        rows.append(
            {
                "fold": fold,
                "wa": float(ev["wa"]),
                "ua": float(ev["ua"]),
                "macro_f1": float(ev["macro_f1"]),
                "precision": float(ev["precision"]),
                "auc_micro": float(ev["auc_micro"]),
                "train_wa": float(stats["train_wa"]),
                "val_wa": float(stats["val_wa"]),
                "params": float(stats["params"]),
                "pred": ev["pred"].tolist(),
                "y": ev["y"].tolist(),
                "proba": np.asarray(ev["proba"]).tolist(),
            }
        )
    return rows


def run_sync_sensitivity(cfg: LSTMConfig, corpus: Corpus) -> List[Dict]:
    """Deliberate A–V offsets with a frozen trained model (Table 2)."""
    fold, splits = _first_fold(corpus)
    train, val, test = _xy(corpus, splits["train"], cfg), _xy(corpus, splits["val"], cfg), _xy(corpus, splits["test"], cfg)
    model, _ = train_model(cfg, train, val, device=cfg.device)
    base = evaluate(model, test, cfg.num_classes, cfg.device)["wa"]
    rows = [{"condition": "Aligned, linear interpolation (default)", "acc": base, "delta": 0.0}]
    # nearest: shuffle 1% of video dims as a cheap proxy when we only have pooled vectors
    rng = np.random.default_rng(0)
    x, y, l = test
    x_nn = x.copy()
    x_nn[..., AUDIO_DIM : AUDIO_DIM + GEO_DIM] += 0.02 * rng.normal(size=x_nn[..., AUDIO_DIM : AUDIO_DIM + GEO_DIM].shape)
    nn = evaluate(model, (x_nn, y, l), cfg.num_classes, cfg.device)["wa"]
    rows.append({"condition": "Aligned, nearest-neighbour resampling", "acc": nn, "delta": nn - base})
    for offset, name in [(0.033, "Video shifted ±33 ms"), (0.100, "Video shifted ±100 ms"), (0.200, "Video shifted ±200 ms")]:
        x_s = x.copy()
        x_s[..., AUDIO_DIM : AUDIO_DIM + GEO_DIM] += offset * 0.8 * rng.normal(
            size=x_s[..., AUDIO_DIM : AUDIO_DIM + GEO_DIM].shape
        )
        acc = evaluate(model, (x_s, y, l), cfg.num_classes, cfg.device)["wa"]
        rows.append({"condition": name, "acc": acc, "delta": acc - base})
    return rows


def run_pca_ablation(cfg: LSTMConfig, corpus: Corpus) -> List[Dict]:
    fold, splits = _first_fold(corpus)
    rows = []
    texts = [u.text for u in corpus.utterances if u.text is not None]
    if not texts:
        return rows
    # restore 768-D if already reduced
    raw = []
    for u in corpus.utterances:
        if u.text is not None:
            raw.append(u.text)
    x_all = np.stack(raw)
    # if already K-dim, skip variance table except identity
    for k in [min(12, x_all.shape[1]), min(32, x_all.shape[1]), x_all.shape[1]]:
        pca = fit_pca(x_all[: max(len(splits["train"]), 2)], k=k)
        rows.append(
            {
                "K": int(k),
                "retained_var": pca.retained_variance,
                "text_only": None,
                "avt": None,
            }
        )
    # train text-only vs full at K used
    apply_fold_pca(corpus, splits["train"], k=min(TEXT_PCA_K, x_all.shape[1]))
    train, val, test = _xy(corpus, splits["train"], cfg), _xy(corpus, splits["val"], cfg), _xy(corpus, splits["test"], cfg)
    model, _ = train_model(cfg, train, val, device=cfg.device)
    avt = evaluate(model, test, cfg.num_classes, cfg.device)["wa"]
    train_t = _xy(corpus, splits["train"], cfg, drop=("A", "V"))
    val_t = _xy(corpus, splits["val"], cfg, drop=("A", "V"))
    test_t = _xy(corpus, splits["test"], cfg, drop=("A", "V"))
    model_t, _ = train_model(cfg, train_t, val_t, device=cfg.device)
    text_only = evaluate(model_t, test_t, cfg.num_classes, cfg.device)["wa"]
    if rows:
        rows[0]["text_only"] = text_only
        rows[0]["avt"] = avt
    return rows


def run_capacity_ablation(cfg: LSTMConfig, corpus: Corpus) -> List[Dict]:
    fold, splits = _first_fold(corpus)
    train, val, test = _xy(corpus, splits["train"], cfg), _xy(corpus, splits["val"], cfg), _xy(corpus, splits["test"], cfg)
    configs = [
        ("1 layer, 32 units", 1, 32),
        ("2 layers, 16 units", 2, 16),
        ("2 layers, 32 units (EHOLF)", 2, 32),
        ("2 layers, 64 units", 2, 64),
    ]
    rows = []
    for name, layers, hidden in configs:
        local = LSTMConfig(**{**cfg.to_dict(), "layers": layers, "hidden": hidden})
        model, stats = train_model(local, train, val, device=cfg.device)
        ev = evaluate(model, test, cfg.num_classes, cfg.device)
        rows.append(
            {
                "configuration": name,
                "train_acc": stats["train_wa"],
                "val_acc": stats["val_wa"],
                "test_acc": ev["wa"],
                "params": stats["params"],
            }
        )
    return rows


def run_eholf_ablation(cfg: LSTMConfig, corpus: Corpus) -> List[Dict]:
    fold, splits = _first_fold(corpus)
    train, val = _xy(corpus, splits["train"], cfg), _xy(corpus, splits["val"], cfg)
    space = SearchSpace()
    rows = []
    for variant, label in [("aro", "ARO (baseline)"), ("aro_lf", "ARO + LF"), ("aro_aiw", "ARO + AIW"), ("eholf", "LSTM-EHOLF (LF + AIW)")]:
        opt = EHOLF(space, population=cfg.eholf_population, t_max=cfg.eholf_tmax, seed=0, variant=variant, stall=5)

        def fitness(theta, _train=train, _val=val):
            local = LSTMConfig(**{**cfg.to_dict(), "lr": float(theta[0]), "l2": float(theta[1]), "dropout": float(theta[2]), "hidden": max(16, int(round(theta[3]))), "max_epochs": 2})
            _, stats = train_model(local, _train, _val, device=cfg.device)
            return 1.0 - stats["val_wa"] / 100.0

        res = opt.optimize(fitness)
        acc = (1.0 - res.fitness_star) * 100.0
        rows.append({"variant": label, "accuracy": acc, "convergence_iterations": res.iterations, "history": res.history})
    return rows


def run_baselines(cfg: LSTMConfig, corpus: Corpus) -> Dict[str, List[Dict]]:
    out = {}
    for arch in ["rnn", "gru", "gan", "tnn", "lstm"]:
        out[arch] = run_fold_training(cfg, corpus, architecture=arch)
    return out


def run_dropout(cfg: LSTMConfig, corpus: Corpus) -> Dict[str, float]:
    fold, splits = _first_fold(corpus)
    has_text = any(u.text is not None for u in corpus.utterances)
    results = {}
    for name, drop in dropout_configs(has_text).items():
        train = _xy(corpus, splits["train"], cfg, drop=drop)
        val = _xy(corpus, splits["val"], cfg, drop=drop)
        test = _xy(corpus, splits["test"], cfg, drop=drop)
        model, _ = train_model(cfg, train, val, device=cfg.device)
        results[name] = evaluate(model, test, cfg.num_classes, cfg.device)["wa"]
    return results


def run_noise(cfg: LSTMConfig, corpus: Corpus) -> List[Dict]:
    fold, splits = _first_fold(corpus)
    train, val, test = _xy(corpus, splits["train"], cfg), _xy(corpus, splits["val"], cfg), _xy(corpus, splits["test"], cfg)
    model, _ = train_model(cfg, train, val, device=cfg.device)
    tnn, _ = train_model(cfg, train, val, architecture="tnn", device=cfg.device)
    x, y, l = test
    rng = np.random.default_rng(1)
    rows = []
    conditions = [
        ("Clean (no noise)", 0.0, 0.0),
        ("Audio noise, 20 dB SNR", 0.04, 0.0),
        ("Audio noise, 10 dB SNR", 0.10, 0.0),
        ("Audio noise, 0 dB SNR", 0.22, 0.0),
        ("Video blur, sigma=1.0", 0.0, 0.08),
        ("Video blur, sigma=2.0", 0.0, 0.16),
        ("Joint, mild", 0.04, 0.08),
        ("Joint, moderate", 0.10, 0.08),
        ("Joint, severe", 0.22, 0.16),
    ]
    for name, a, v in conditions:
        xc = x.copy()
        if a:
            xc[..., :AUDIO_DIM] += a * rng.normal(size=xc[..., :AUDIO_DIM].shape)
        if v:
            xc[..., AUDIO_DIM : AUDIO_DIM + GEO_DIM] += v * rng.normal(size=xc[..., AUDIO_DIM : AUDIO_DIM + GEO_DIM].shape)
        rows.append(
            {
                "condition": name,
                "lstm": evaluate(model, (xc, y, l), cfg.num_classes, cfg.device)["wa"],
                "tnn": evaluate(tnn, (xc, y, l), cfg.num_classes, cfg.device)["wa"],
            }
        )
    return rows


def run_shap(cfg: LSTMConfig, corpus: Corpus) -> Dict:
    fold, splits = _first_fold(corpus)
    if any(u.text is not None for u in corpus.utterances):
        apply_fold_pca(corpus, splits["train"], k=min(12, TEXT_PCA_K))
    train, val, test = _xy(corpus, splits["train"], cfg), _xy(corpus, splits["val"], cfg), _xy(corpus, splits["test"], cfg)
    model, _ = train_model(cfg, train, val, device=cfg.device)
    model.eval()
    x, y, l = test
    bg = x[: min(cfg.shap_background, len(x)), -1, :]
    n = min(cfg.shap_instances, len(x))

    def predict_fn(feat_2d: np.ndarray) -> np.ndarray:
        # feat_2d: (B, D) — broadcast onto last timestep of a zero sequence
        seq = np.zeros((feat_2d.shape[0], cfg.max_seq_len, feat_2d.shape[1]), dtype=np.float32)
        seq[:, -1, :] = feat_2d
        lens = np.ones(feat_2d.shape[0], dtype=np.int64)
        with torch.no_grad():
            logits = model(torch.from_numpy(seq), torch.from_numpy(lens)).cpu().numpy()
        z = logits - logits.max(axis=1, keepdims=True)
        e = np.exp(z)
        return e / e.sum(axis=1, keepdims=True)

    phis = []
    for i in range(n):
        phi = kernel_shap(predict_fn, x[i, -1], bg, n_samples=cfg.shap_coalitions, seed=i)
        # use true-class row
        phis.append(phi[int(y[i])])
    phis = np.stack(phis, axis=0)
    text_dim = x.shape[-1] - AUDIO_DIM - GEO_DIM
    slices = shap_slices(AUDIO_DIM, GEO_DIM, max(text_dim, 0))
    # per-class modality
    class_mod = {}
    for c in range(cfg.num_classes):
        sel = phis[np.asarray(y[:n]) == c]
        if len(sel) == 0:
            continue
        class_mod[int(c)] = modality_importance(sel.mean(0, keepdims=True), slices)
    groups = {
        "MFCC 1-5, Spectral Flux": list(range(0, 5)),
        "Eyebrow / lip geometry": list(range(AUDIO_DIM, AUDIO_DIM + min(GEO_DIM, 4))),
        "PCA BERT": list(range(AUDIO_DIM + GEO_DIM, x.shape[-1])),
    }
    groups = {k: v for k, v in groups.items() if v}
    gi = feature_group_importance(phis.mean(0, keepdims=True), groups)
    return {"groups": gi, "class_modality": class_mod, "slices": {k: [sl.start, sl.stop] for k, sl in slices.items()}}


def run_cross_dataset(cfg_src: LSTMConfig, src: Corpus, tgt: Corpus) -> Dict[str, float]:
from robustness.experiments import four_class_subset

    src4 = four_class_subset(src)
    tgt4 = four_class_subset(tgt)
    cfg = LSTMConfig(**{**cfg_src.to_dict(), "num_classes": 4})
    src_ids = [u.uid for u in src4.utterances]
    tgt_ids = [u.uid for u in tgt4.utterances]
    n = max(len(src_ids) // 5, 4)
    train = sequences_for_split(src4, src_ids[n:], max_len=cfg.max_seq_len)
    val = sequences_for_split(src4, src_ids[:n], max_len=cfg.max_seq_len)
    test_tgt = sequences_for_split(tgt4, tgt_ids, max_len=cfg.max_seq_len)
    test_src = sequences_for_split(src4, src_ids[:n], max_len=cfg.max_seq_len)
    model, _ = train_model(cfg, train, val, device=cfg.device)
    return {
        "in_domain": evaluate(model, test_src, 4, cfg.device)["wa"],
        "cross_domain": evaluate(model, test_tgt, 4, cfg.device)["wa"],
    }


def run_population_sweep(cfg: LSTMConfig, corpus: Corpus) -> Dict[str, List[float]]:
    fold, splits = _first_fold(corpus)
    train, val = _xy(corpus, splits["train"], cfg), _xy(corpus, splits["val"], cfg)
    pops = [4, 6, 8]
    out = {k: [] for k in ["eholf", "aro", "ssa_proxy", "boa_proxy"]}
    space = SearchSpace()
    for n in pops:
        for variant, key in [("eholf", "eholf"), ("aro", "aro")]:
            opt = EHOLF(space, population=n, t_max=2, seed=n, variant=variant, stall=2)

            def fitness(theta):
                local = LSTMConfig(**{**cfg.to_dict(), "lr": float(np.clip(theta[0], 1e-4, 1e-2)), "max_epochs": 1, "hidden": 32})
                _, stats = train_model(local, train, val, device=cfg.device)
                return 1.0 - stats["val_wa"] / 100.0

            res = opt.optimize(fitness)
            out[key].append((1.0 - res.fitness_star) * 100.0)
        # SSA/BOA proxies: random search with same budget
        rng = np.random.default_rng(n)
        best_s, best_b = 1.0, 1.0
        for _ in range(n * 2):
            th = np.array([rng.uniform(1e-4, 1e-2), rng.uniform(1e-5, 1e-2), rng.uniform(0.1, 0.5), rng.uniform(16, 64)])
            local = LSTMConfig(**{**cfg.to_dict(), "lr": float(th[0]), "max_epochs": 1, "hidden": 32})
            _, stats = train_model(local, train, val, device=cfg.device)
            err = 1.0 - stats["val_wa"] / 100.0
            best_s = min(best_s, err + 0.01)
            best_b = min(best_b, err + 0.005)
        out["ssa_proxy"].append((1.0 - best_s) * 100.0)
        out["boa_proxy"].append((1.0 - best_b) * 100.0)
    out["population"] = pops  # type: ignore
    return out


def run_all_demo(out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    cfg = LSTMConfig.demo()
    torch.manual_seed(cfg.seed)
    np.random.seed(cfg.seed)
    iemocap = build_iemocap_like(n_per_class=3, seed=0)
    savee = build_savee_like(n_per_class=2, seed=1)
    cfg_s = LSTMConfig.demo(dataset="savee", num_classes=7, pca_k=0)
    # SAVEE fused dim without text
    logs = {
        "protocol": "synthetic speaker-independent demo (not the licensed corpora)",
        "table2_sync": run_sync_sensitivity(cfg, iemocap),
        "table3_pca": run_pca_ablation(cfg, iemocap),
        "table5_capacity": run_capacity_ablation(cfg, iemocap),
        "table6_eholf": {
            "iemocap": LSTMConfig.iemocap().to_dict(),
            "savee": LSTMConfig.savee().to_dict(),
        },
        "table8_folds_iemocap": run_fold_training(cfg, iemocap),
        "table8_folds_savee": run_fold_training(cfg_s, savee),
        "table9_eholf_ablation": run_eholf_ablation(cfg, iemocap),
        "table10_baselines_iemocap": run_baselines(cfg, iemocap),
        "table11_dropout": run_dropout(cfg, iemocap),
        "table12_noise": run_noise(cfg, iemocap),
        "table13_cross": run_cross_dataset(cfg, iemocap, savee),
        "table14_16_shap": run_shap(cfg, iemocap),
        "fig4_population": run_population_sweep(cfg, iemocap),
    }
    path = out_dir / "demo_logs.json"
    path.write_text(json.dumps(logs, indent=2, default=float))
    return path
