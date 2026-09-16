#!/usr/bin/env python3
"""Build utterance-level LOSO / speaker-independent split JSON from licensed corpora."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


IEMOCAP4 = {"neu": "neutral", "sad": "sad", "hap": "happy", "exc": "happy", "ang": "angry"}
SAVEE_MAP = {
    "n": "neutral",
    "sa": "sad",
    "a": "angry",
    "h": "happy",
    "su": "surprise",
    "f": "fear",
    "d": "disgust",
}


def parse_iemocap_emotion(emo_file: Path) -> dict:
    mapping = {}
    current = None
    for line in emo_file.read_text(errors="ignore").splitlines():
        line = line.strip()
        if line.startswith("[") and "\t" in line:
            parts = line.split()
            # [START - END]  utt_id  emo  [V, A, D]
            if len(parts) >= 3:
                utt = parts[2] if parts[1] == "-" else parts[1]
                # typical: [6.2901 - 8.2357]\tSes01F_impro01_F000\tneu\t[2.5000, 2.5000, 2.5000]
        if "\t" in line and line.startswith("["):
            bits = line.split("\t")
            if len(bits) >= 3:
                utt = bits[1].strip()
                lab = bits[2].strip()
                if lab in IEMOCAP4:
                    mapping[utt] = IEMOCAP4[lab]
    return mapping


def iemocap_splits(root: Path) -> dict:
    sessions = [f"Ses0{i}" for i in range(1, 6)]
    by_session = {s: [] for s in sessions}
    emo_root = root / "IEMOCAP_full_release" if (root / "IEMOCAP_full_release").exists() else root
    for ses in sessions:
        ses_dir = None
        for cand in emo_root.glob(f"Session{int(ses[-1])}**/EmoEvaluation/*.txt"):
            mapping = parse_iemocap_emotion(cand)
            for utt, lab in mapping.items():
                by_session[ses].append({"id": utt, "label": lab, "session": ses})
        # simpler glob
        folder = emo_root / f"Session{int(ses[-1])}" / "dialog" / "EmoEvaluation"
        if folder.exists():
            by_session[ses] = []
            for txt in folder.glob("*.txt"):
                if txt.name.startswith("._"):
                    continue
                for utt, lab in parse_iemocap_emotion(txt).items():
                    speaker = utt.split("_")[-1][0]  # F/M of last token
                    by_session[ses].append({"id": utt, "label": lab, "session": ses, "speaker": f"{ses}_{speaker}"})
    folds = {}
    for test in sessions:
        rest = [s for s in sessions if s != test]
        val = rest[-1]
        train = rest[:-1]
        folds[test] = {
            "train": [u["id"] for s in train for u in by_session[s]],
            "val": [u["id"] for u in by_session[val]],
            "test": [u["id"] for u in by_session[test]],
        }
    return {"protocol": "5-fold LOSO", "folds": folds, "sessions": sessions}


def savee_splits(root: Path) -> dict:
    speakers = ["DC", "JE", "JK", "KL"]
    items = {s: [] for s in speakers}
    audio = root / "AudioData" if (root / "AudioData").exists() else root
    for spk in speakers:
        folder = audio / spk
        if not folder.exists():
            continue
        for wav in sorted(folder.glob("*.wav")):
            stem = wav.stem.lower()
            lab = None
            for key, name in sorted(SAVEE_MAP.items(), key=lambda kv: -len(kv[0])):
                if stem.startswith(key):
                    lab = name
                    break
            if lab:
                items[spk].append({"id": f"{spk}/{wav.name}", "label": lab, "speaker": spk})
    folds = {}
    for test in speakers:
        rest = [s for s in speakers if s != test]
        val = rest[-1]
        train = rest[:-1]
        folds[test] = {
            "train": [u["id"] for s in train for u in items[s]],
            "val": [u["id"] for u in items[val]],
            "test": [u["id"] for u in items[test]],
        }
    return {"protocol": "4-fold speaker-independent", "folds": folds, "speakers": speakers}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--iemocap", type=Path)
    p.add_argument("--savee", type=Path)
    p.add_argument("--out", type=Path, default=Path("splits"))
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.iemocap:
        data = iemocap_splits(args.iemocap)
        (args.out / "iemocap_loso_utterances.json").write_text(json.dumps(data, indent=2))
        print("IEMOCAP folds written")
    if args.savee:
        data = savee_splits(args.savee)
        (args.out / "savee_speaker_utterances.json").write_text(json.dumps(data, indent=2))
        print("SAVEE folds written")
    if not args.iemocap and not args.savee:
        print("Pass --iemocap and/or --savee pointing at the licensed corpus roots.")


if __name__ == "__main__":
    main()
