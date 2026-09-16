"""Synthetic multimodal utterances for leakage-controlled speaker-independent folds."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from lstm_eholf.config import (
    AUDIO_DIM,
    GEO_DIM,
    IEMOCAP_EMOTIONS,
    SAVEE_EMOTIONS,
    TEXT_BERT_DIM,
    TEXT_PCA_K,
)
from preprocessing.text import fit_pca, hash_embed_tokens


EMOTION_OFFSETS = {
    "neutral": 0.0,
    "sad": 1.0,
    "happy": 2.0,
    "angry": 3.0,
    "surprise": 4.0,
    "fear": 5.0,
    "disgust": 6.0,
}


@dataclass
class Utterance:
    uid: str
    speaker: str
    session: str
    dialogue: str
    label: str
    label_id: int
    audio: np.ndarray
    video: np.ndarray
    text: Optional[np.ndarray]
    text_raw: Optional[np.ndarray]
    transcript: str
    waveform: np.ndarray
    landmarks: np.ndarray  # (T, 68, 2)


@dataclass
class Corpus:
    name: str
    emotions: Tuple[str, ...]
    utterances: List[Utterance]
    folds: Dict[str, Dict[str, List[str]]]  # fold -> {train, val, test} -> uids

    def by_id(self) -> Dict[str, Utterance]:
        return {u.uid: u for u in self.utterances}


def _emotion_signal(label: str, dim: int, rng: np.random.Generator) -> np.ndarray:
    base = np.linspace(-1, 1, dim)
    k = EMOTION_OFFSETS[label]
    return np.sin(base * (k + 1) + k) + 0.15 * rng.normal(size=dim)


def make_landmarks(label: str, n_frames: int, rng: np.random.Generator) -> np.ndarray:
    t = np.linspace(0, 1, 68)
    face = np.stack([np.cos(2 * np.pi * t), np.sin(2 * np.pi * t)], axis=1)
    k = EMOTION_OFFSETS[label]
    frames = []
    for i in range(n_frames):
        jitter = 0.02 * rng.normal(size=face.shape)
        expr = 0.05 * k * np.stack([np.sin(np.arange(68) / 10.0 + i * 0.1), np.cos(np.arange(68) / 8.0)], axis=1)
        frames.append(face + jitter + expr)
    return np.stack(frames, axis=0)


def make_waveform(label: str, sr: int, seconds: float, rng: np.random.Generator) -> np.ndarray:
    n = int(sr * seconds)
    t = np.arange(n) / sr
    f0 = 120 + 40 * EMOTION_OFFSETS[label]
    return (0.2 * np.sin(2 * np.pi * f0 * t) + 0.05 * rng.normal(size=n)).astype(np.float32)


def _split_speakers(speakers: Sequence[str], test_spk: str) -> Tuple[List[str], List[str], str]:
    rest = [s for s in speakers if s != test_spk]
    val = rest[-1]
    train = rest[:-1]
    return train, [val], test_spk


def build_iemocap_like(n_per_class: int = 8, seed: int = 0, use_text: bool = True) -> Corpus:
    rng = np.random.default_rng(seed)
    sessions = [f"Ses0{i}" for i in range(1, 6)]
    # two speakers per session
    speakers = []
    utterances: List[Utterance] = []
    emotions = IEMOCAP_EMOTIONS
    uid = 0
    transcripts = {
        "neutral": "the weather is fine today",
        "sad": "i feel so empty and tired",
        "happy": "this is wonderful news",
        "angry": "stop doing that right now",
    }
    for ses in sessions:
        spk_a, spk_b = f"{ses}_F", f"{ses}_M"
        speakers.extend([spk_a, spk_b])
        for spk in (spk_a, spk_b):
            for lab_id, lab in enumerate(emotions):
                for k in range(n_per_class):
                    audio = _emotion_signal(lab, AUDIO_DIM, rng) + 0.01 * (sum(map(ord, spk)) % 7)
                    video = _emotion_signal(lab, GEO_DIM, rng)
                    text = hash_embed_tokens(transcripts[lab].split() + [spk, str(k)], seed=seed) if use_text else None
                    utt = Utterance(
                        uid=f"{ses}_{spk}_{lab}_{k}",
                        speaker=spk,
                        session=ses,
                        dialogue=f"{ses}_{spk}",
                        label=lab,
                        label_id=lab_id,
                        audio=audio.astype(np.float32),
                        video=video.astype(np.float32),
                        text=text,
                        text_raw=None if text is None else text.copy(),
                        transcript=transcripts[lab],
                        waveform=make_waveform(lab, 16000, 0.4, rng),
                        landmarks=make_landmarks(lab, 8, rng),
                    )
                    utterances.append(utt)
                    uid += 1
    folds: Dict[str, Dict[str, List[str]]] = {}
    by_session: Dict[str, List[Utterance]] = {s: [] for s in sessions}
    for u in utterances:
        by_session[u.session].append(u)
    for test_ses in sessions:
        train_ses = [s for s in sessions if s != test_ses]
        val_ses = train_ses[-1]
        train_ses = train_ses[:-1]
        folds[test_ses] = {
            "train": [u.uid for s in train_ses for u in by_session[s]],
            "val": [u.uid for u in by_session[val_ses]],
            "test": [u.uid for u in by_session[test_ses]],
        }
    return Corpus("iemocap_demo", emotions, utterances, folds)


def build_savee_like(n_per_class: int = 4, seed: int = 1) -> Corpus:
    rng = np.random.default_rng(seed)
    speakers = ["DC", "JE", "JK", "KL"]
    emotions = SAVEE_EMOTIONS
    utterances: List[Utterance] = []
    for spk in speakers:
        for lab_id, lab in enumerate(emotions):
            for k in range(n_per_class):
                audio = _emotion_signal(lab, AUDIO_DIM, rng)
                video = _emotion_signal(lab, GEO_DIM, rng)
                utterances.append(
                    Utterance(
                        uid=f"{spk}_{lab}_{k}",
                        speaker=spk,
                        session=spk,
                        dialogue=spk,
                        label=lab,
                        label_id=lab_id,
                        audio=audio.astype(np.float32),
                        video=video.astype(np.float32),
                        text=None,
                        text_raw=None,
                        transcript="",
                        waveform=make_waveform(lab, 16000, 0.3, rng),
                        landmarks=make_landmarks(lab, 6, rng),
                    )
                )
    folds = {}
    by_spk = {s: [u for u in utterances if u.speaker == s] for s in speakers}
    for test in speakers:
        rest = [s for s in speakers if s != test]
        val = rest[-1]
        train = rest[:-1]
        folds[test] = {
            "train": [u.uid for s in train for u in by_spk[s]],
            "val": [u.uid for u in by_spk[val]],
            "test": [u.uid for u in by_spk[test]],
        }
    return Corpus("savee_demo", emotions, utterances, folds)


def apply_fold_pca(corpus: Corpus, train_ids: Sequence[str], k: int = TEXT_PCA_K) -> None:
    by_id = corpus.by_id()
    train_x = np.stack(
        [
            (by_id[i].text_raw if by_id[i].text_raw is not None else by_id[i].text)
            for i in train_ids
            if (by_id[i].text_raw is not None or by_id[i].text is not None)
        ]
    )
    pca = fit_pca(train_x, k=k)
    for u in corpus.utterances:
        src = u.text_raw if u.text_raw is not None else u.text
        if src is not None:
            u.text = pca.transform(src)
    corpus.pca = pca  # type: ignore[attr-defined]


def fused_vector(u: Utterance, drop: Optional[Sequence[str]] = None) -> np.ndarray:
    drop = set(drop or [])
    parts = []
    if "A" not in drop:
        parts.append(u.audio)
    else:
        parts.append(np.zeros_like(u.audio))
    if "V" not in drop:
        parts.append(u.video)
    else:
        parts.append(np.zeros_like(u.video))
    if u.text is not None:
        if "T" not in drop:
            parts.append(u.text)
        else:
            parts.append(np.zeros_like(u.text))
    return np.concatenate(parts).astype(np.float32)


def sequences_for_split(
    corpus: Corpus,
    uids: Sequence[str],
    max_len: int = 8,
    drop: Optional[Sequence[str]] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Group utterances by dialogue; pad to max_len. Labels are last-utterance labels."""
    by_id = corpus.by_id()
    groups: Dict[str, List[Utterance]] = {}
    for uid in uids:
        u = by_id[uid]
        groups.setdefault(u.dialogue, []).append(u)
    xs, ys, lens = [], [], []
    dim = fused_vector(next(iter(by_id.values())), drop).shape[0]
    for dlg, utts in groups.items():
        utts = sorted(utts, key=lambda z: z.uid)
        # one sequence per utterance (length-1) plus a short dialogue window
        for i, u in enumerate(utts):
            window = utts[max(0, i - max_len + 1) : i + 1]
            feat = np.stack([fused_vector(w, drop) for w in window], axis=0)
            pad = np.zeros((max_len, dim), dtype=np.float32)
            n = min(len(window), max_len)
            pad[-n:] = feat[-n:]
            xs.append(pad)
            ys.append(u.label_id)
            lens.append(n)
    return np.stack(xs), np.asarray(ys, dtype=np.int64), np.asarray(lens, dtype=np.int64)
