# MR-AVT for Speech Communication

Complete methodology and PyTorch implementation of **Multi-Resolution Audio--Visual Transformer with Heterogeneous Graph Fusion for Robust Speech Emotion Recognition**, prepared for *Speech Communication* (Elsevier).

## What is in this repository

- `docs/METHODOLOGY.md` — full methodological specification (tensors, losses, protocols).
- `paper/method_section.tex` — journal-ready method section, including the completed \(\mathcal{L}_{\mathrm{cm}}\) definition.
- `paper/references.bib` — bibliography skeleton for the manuscript.
- `mr_avt/` — end-to-end model, losses, data I/O, training, and robustness evaluation.
- `configs/default.yaml` — hyperparameters from the manuscript.
- `tests/` — architecture, gate, missing-modality, and CPU training smoke tests.

The three audio temporal branches (25 / 100 / 500 ms), heterogeneous GAT, uncertainty fusion, pre-gating, and the six-term training objective match the paper. Reported benchmark numbers in the manuscript require the licensed AFEW5.0, BAUM-1s, and IEMOCAP releases; this code does not redistribute those corpora.

## Install

```bash
pip install -r requirements.txt
pip install -e .
```

`pyproject.toml` is provided so that `import mr_avt` works from any working directory.

## Data manifest

Training expects a CSV (or JSON list) with columns:

```text
audio,video,label,speaker,session,split
```

- `label` is an integer in the dataset label space (AFEW: 0–6, BAUM-1s: 0–5, IEMOCAP 4-class: 0–3 with excited merged into happy).
- `split` is `train`, `val`, or `test`.
- IEMOCAP leave-one-session-out uses the `session` field; BAUM-1s LOSGO uses `speaker`.

Synthetic smoke data:

```bash
python scripts/make_synthetic_manifest.py --out data/synthetic
python train.py --tiny --manifest data/synthetic/manifest.csv --output outputs/smoke --device cpu --num-classes 4
```

The synthetic generator writes short sinusoids and random frame tensors. It is for pipeline checks, not for reproducing Table 1.

## Train / evaluate

Paper-sized model (ViT-B/16 width, 6-layer audio transformers):

```bash
python train.py --config configs/default.yaml --manifest data/iemocap/manifest.csv --output outputs/iemocap
python evaluate.py --config configs/default.yaml --manifest data/iemocap/manifest.csv --checkpoint outputs/iemocap/best.pt --robustness
```

Early stopping monitors unweighted accuracy on BAUM-1s / IEMOCAP and accuracy on AFEW5.0, as in the manuscript.

## Tests

```bash
python -m pytest tests -q
```

Tests use `MRAVTConfig.tiny()` so they run on CPU without pretrained weights.

## Protocol reminder

Do not average or rank AFEW5.0, BAUM-1s, and IEMOCAP together. They differ in label space, split construction, and official metric. Robustness figures are within-model analyses under the corruption schedule in `docs/METHODOLOGY.md`.
