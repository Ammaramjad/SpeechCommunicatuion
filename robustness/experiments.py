"""Modality dropout, noise, joint corruption, and four-class cross-dataset transfer."""

from __future__ import annotations

from typing import Dict, Optional, Sequence, Tuple

import numpy as np
import torch

from lstm_eholf.config import SHARED4
from lstm_eholf.data import Corpus, Utterance, fused_vector, sequences_for_split
from lstm_eholf.train import evaluate
from preprocessing.audio import add_awgn
from preprocessing.video import gaussian_blur_frames


def dropout_configs(has_text: bool) -> Dict[str, Sequence[str]]:
    cfg = {
        "A": ("V", "T") if has_text else ("V",),
        "V": ("A", "T") if has_text else ("A",),
        "A+V": ("T",) if has_text else (),
        "full": (),
    }
    if has_text:
        cfg["T"] = ("A", "V")
        cfg["A+T"] = ("V",)
        cfg["V+T"] = ("A",)
        cfg["A+V+T"] = ()
    return cfg


def mask_text_tokens(text: str, rate: float, rng: np.random.Generator) -> str:
    toks = text.split()
    out = []
    vocab = ["the", "a", "unk", "xx", "yy"]
    for t in toks:
        if rng.random() < rate:
            out.append(str(rng.choice(vocab)))
        else:
            out.append(t)
    return " ".join(out)


def four_class_subset(corpus: Corpus) -> Corpus:
    keep = [u for u in corpus.utterances if u.label in SHARED4]
    mapping = {lab: i for i, lab in enumerate(SHARED4)}
    for u in keep:
        u.label_id = mapping[u.label]
    folds = {}
    for name, split in corpus.folds.items():
        folds[name] = {k: [uid for uid in v if any(u.uid == uid and u.label in SHARED4 for u in keep)] for k, v in split.items()}
    return Corpus(corpus.name + "_4", SHARED4, keep, folds)


def cross_domain_xy(source: Corpus, target: Corpus, max_len: int):
    src_all = [u.uid for u in source.utterances if u.label in SHARED4]
    tgt_all = [u.uid for u in target.utterances if u.label in SHARED4]
    # remap labels
    for corp in (source, target):
        m = {lab: i for i, lab in enumerate(SHARED4)}
        for u in corp.utterances:
            if u.label in SHARED4:
                u.label_id = m[u.label]
    return sequences_for_split(source, src_all, max_len), sequences_for_split(target, tgt_all, max_len)
