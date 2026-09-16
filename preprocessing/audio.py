"""MFCC (13) + delta + delta-delta and spectral descriptors; utterance mean/std -> 78-D."""

from __future__ import annotations

import numpy as np


def _frame_signal(x: np.ndarray, win: int, hop: int) -> np.ndarray:
    if x.ndim != 1:
        x = np.asarray(x).reshape(-1)
    n = x.shape[0]
    if n < win:
        x = np.pad(x, (0, win - n))
        n = x.shape[0]
    n_frames = 1 + (n - win) // hop
    frames = np.lib.stride_tricks.as_strided(
        x,
        shape=(n_frames, win),
        strides=(x.strides[0] * hop, x.strides[0]),
        writeable=False,
    )
    window = np.hamming(win)
    return frames * window


def _power_spectrum(frames: np.ndarray, n_fft: int) -> np.ndarray:
    spec = np.fft.rfft(frames, n=n_fft, axis=-1)
    return np.abs(spec) ** 2


def _mel_filterbank(sr: int, n_fft: int, n_mels: int = 26, fmin: float = 0.0, fmax: float | None = None) -> np.ndarray:
    fmax = fmax or sr / 2.0

    def hz2mel(f):
        return 2595.0 * np.log10(1.0 + f / 700.0)

    def mel2hz(m):
        return 700.0 * (10 ** (m / 2595.0) - 1.0)

    mels = np.linspace(hz2mel(fmin), hz2mel(fmax), n_mels + 2)
    hz = mel2hz(mels)
    bins = np.floor((n_fft + 1) * hz / sr).astype(int)
    fb = np.zeros((n_mels, n_fft // 2 + 1))
    for i in range(n_mels):
        left, center, right = bins[i], bins[i + 1], bins[i + 2]
        if center == left:
            center += 1
        if right == center:
            right += 1
        for j in range(left, center):
            if 0 <= j < fb.shape[1]:
                fb[i, j] = (j - left) / max(center - left, 1)
        for j in range(center, right):
            if 0 <= j < fb.shape[1]:
                fb[i, j] = (right - j) / max(right - center, 1)
    return fb


def _dct(x: np.ndarray, n_mfcc: int) -> np.ndarray:
    n = x.shape[-1]
    k = np.arange(n_mfcc)[:, None]
    n_idx = np.arange(n)[None, :]
    basis = np.cos(np.pi * k * (n_idx + 0.5) / n)
    basis[0] *= 1.0 / np.sqrt(2.0)
    return np.sqrt(2.0 / n) * (x @ basis.T)


def _delta(feat: np.ndarray, width: int = 2) -> np.ndarray:
    pad = np.pad(feat, ((width, width), (0, 0)), mode="edge")
    denom = 2 * sum(i * i for i in range(1, width + 1))
    out = np.zeros_like(feat)
    for t in range(feat.shape[0]):
        acc = 0.0
        for i in range(1, width + 1):
            acc = acc + i * (pad[t + width + i] - pad[t + width - i])
        out[t] = acc / denom
    return out


def _spectral_descriptors(power: np.ndarray, sr: int, n_fft: int) -> np.ndarray:
    freqs = np.linspace(0, sr / 2.0, power.shape[-1])
    p = power + 1e-12
    centroid = (p * freqs).sum(axis=-1) / p.sum(axis=-1)
    cum = np.cumsum(p, axis=-1)
    rolloff = np.zeros(p.shape[0])
    for i, c in enumerate(cum):
        thr = 0.85 * c[-1]
        idx = int(np.searchsorted(c, thr))
        rolloff[i] = freqs[min(idx, len(freqs) - 1)]
    flux = np.sqrt(np.maximum(np.diff(p, axis=0, prepend=p[:1]), 0.0).sum(axis=-1))
    return np.stack([centroid, rolloff, flux], axis=-1)


def extract_frame_features(
    waveform: np.ndarray,
    sr: int = 16000,
    win_ms: float = 25.0,
    hop_ms: float = 10.0,
) -> np.ndarray:
    """Return (T, 42) frame features: 39 MFCC-family + 3 spectral descriptors."""
    x = np.asarray(waveform, dtype=np.float64).reshape(-1)
    if x.size == 0:
        x = np.zeros(int(sr * 0.3))
    x = x / (np.max(np.abs(x)) + 1e-8)
    win = int(sr * win_ms / 1000.0)
    hop = int(sr * hop_ms / 1000.0)
    n_fft = 512
    frames = _frame_signal(x, win, hop)
    power = _power_spectrum(frames, n_fft)
    fb = _mel_filterbank(sr, n_fft)
    logmel = np.log(power @ fb.T + 1e-10)
    mfcc = _dct(logmel, 13)
    d1 = _delta(mfcc)
    d2 = _delta(d1)
    spec = _spectral_descriptors(power, sr, n_fft)
    return np.concatenate([mfcc, d1, d2, spec], axis=-1)


def extract_audio_features(waveform: np.ndarray, sr: int = 16000) -> np.ndarray:
    """Utterance-level 78-D vector: mean and std of 39 MFCC-family coefficients.

    Spectral descriptors are included in the frame stream used for alignment;
    the manuscript pools MFCC/delta/delta-delta (39) with mean and std (78).
    """
    frames = extract_frame_features(waveform, sr=sr)
    mfcc_family = frames[:, :39]
    mean = mfcc_family.mean(axis=0)
    std = mfcc_family.std(axis=0)
    return np.concatenate([mean, std]).astype(np.float32)


def add_awgn(waveform: np.ndarray, snr_db: float, rng: np.random.Generator | None = None) -> np.ndarray:
    rng = rng or np.random.default_rng(0)
    x = np.asarray(waveform, dtype=np.float64)
    power = np.mean(x ** 2) + 1e-12
    noise_power = power / (10 ** (snr_db / 10.0))
    noise = rng.normal(0.0, np.sqrt(noise_power), size=x.shape)
    return (x + noise).astype(x.dtype)
