"""Unit tests for LSTM-EHOLF methodology modules."""

from __future__ import annotations

import numpy as np

from eholf.optimizer import EHOLF, levy_sigma
from explain.kernel_shap import kernel_shap, modality_importance, shap_slices
from lstm_eholf.config import AUDIO_DIM, LSTMConfig
from lstm_eholf.data import build_iemocap_like, sequences_for_split
from lstm_eholf.metrics import fold_std
from lstm_eholf.models import count_parameters
from lstm_eholf.train import evaluate, train_model
from preprocessing.alignment import align_audio_video, piecewise_linear_resample
from preprocessing.audio import extract_audio_features
from preprocessing.text import fit_pca
from preprocessing.video import geometric_from_landmarks


def test_mfcc_dim():
    rng = np.random.default_rng(0)
    wav = rng.normal(size=16000)
    feat = extract_audio_features(wav, sr=16000)
    assert feat.shape == (AUDIO_DIM,)


def test_geometric_landmarks_dim():
    from lstm_eholf.data import make_landmarks

    rng = np.random.default_rng(0)
    pts = make_landmarks("happy", 1, rng)[0]
    geo = geometric_from_landmarks(pts)
    assert geo.shape == (8,)


def test_linear_align_identity():
    t = np.linspace(0, 1, 10)
    v = np.stack([t, t ** 2], axis=1)
    dst = np.linspace(0, 1, 10)
    rec = piecewise_linear_resample(v, t, dst)
    assert np.allclose(rec, v, atol=1e-6)


def test_audio_video_align_length():
    audio = np.random.randn(50, 5)
    video = np.random.randn(15, 4)
    a, v = align_audio_video(audio, video, hop_s=0.01, fps=30.0)
    assert a.shape[0] == v.shape[0] == 50
    assert v.shape[1] == 4


def test_pca_variance_increases_with_k():
    rng = np.random.default_rng(1)
    x = rng.normal(size=(40, 32))
    p4 = fit_pca(x, k=4)
    p8 = fit_pca(x, k=8)
    assert p8.retained_variance > p4.retained_variance
    z = p4.transform(x)
    assert z.shape == (40, 4)


def test_levy_sigma_beta():
    s = levy_sigma(1.5)
    assert 0.5 < s < 1.5


def test_eholf_quadratic():
    def f(theta):
        target = np.array([0.001, 0.001, 0.3, 128.0])
        return float(np.mean((theta - target) ** 2))

    opt = EHOLF(population=8, t_max=25, seed=2, stall=8)
    res = opt.optimize(f)
    assert res.fitness_star < f(opt._sample())
    assert res.history[-1] <= res.history[0]


def test_lstm_trains_on_demo():
    cfg = LSTMConfig.demo(max_epochs=2)
    corpus = build_iemocap_like(n_per_class=2, seed=0)
    fold = corpus.folds["Ses01"]
    train = sequences_for_split(corpus, fold["train"], max_len=cfg.max_seq_len)
    val = sequences_for_split(corpus, fold["val"], max_len=cfg.max_seq_len)
    test = sequences_for_split(corpus, fold["test"], max_len=cfg.max_seq_len)
    model, stats = train_model(cfg, train, val, device="cpu")
    ev = evaluate(model, test, cfg.num_classes, "cpu")
    assert 0.0 <= ev["wa"] <= 100.0
    assert count_parameters(model) > 0
    assert stats["params"] > 0


def test_kernel_shap_shape():
    rng = np.random.default_rng(0)
    w = rng.normal(size=(4, 6))

    def predict(x):
        logits = x @ w.T
        z = logits - logits.max(axis=1, keepdims=True)
        e = np.exp(z)
        return e / e.sum(axis=1, keepdims=True)

    x = rng.normal(size=6)
    bg = rng.normal(size=(12, 6))
    phi = kernel_shap(predict, x, bg, n_samples=64, seed=0)
    assert phi.shape == (4, 6)
    sl = shap_slices(2, 2, 2)
    imp = modality_importance(phi, sl)
    assert abs(sum(imp.values()) - 100.0) < 1e-6


def test_fold_std_matches_paper_iemocap_wa():
    wa = [87.9, 85.4, 86.1, 88.2, 85.9]
    mean, sd = fold_std(wa)
    assert abs(mean - 86.7) < 0.05
    assert abs(sd - 1.3) < 0.06
