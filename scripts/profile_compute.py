#!/usr/bin/env python3
"""Re-measure wall-clock costs on this machine (Table 7 is hardware-specific)."""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import torch

from lstm_eholf.config import LSTMConfig
from lstm_eholf.data import build_iemocap_like, sequences_for_split
from lstm_eholf.models import LSTMClassifier, count_parameters
from lstm_eholf.train import train_model
from preprocessing.audio import extract_audio_features


def main():
    cfg = LSTMConfig.demo()
    corpus = build_iemocap_like(n_per_class=2, seed=0)
    u = corpus.utterances[0]
    t0 = time.perf_counter()
    extract_audio_features(u.waveform)
    audio_ms = (time.perf_counter() - t0) * 1000
    fold = next(iter(corpus.folds.values()))
    train = sequences_for_split(corpus, fold["train"], max_len=cfg.max_seq_len)
    val = sequences_for_split(corpus, fold["val"], max_len=cfg.max_seq_len)
    t1 = time.perf_counter()
    model, stats = train_model(cfg, train, val, device="cpu")
    train_s = time.perf_counter() - t1
    x = torch.from_numpy(train[0][:1])
    t2 = time.perf_counter()
    with torch.no_grad():
        model(x)
    inf_ms = (time.perf_counter() - t2) * 1000
    out = {
        "note": "Demo-scale timings on the current host. Manuscript Table 7 used RTX 4070 Ti + i7-13700K on full IEMOCAP/SAVEE.",
        "audio_feature_ms": audio_ms,
        "demo_train_s": train_s,
        "lstm_infer_ms": inf_ms,
        "params": stats["params"],
        "param_count_fn": count_parameters(model),
    }
    dest = Path("results/local_compute.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
