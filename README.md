# MR-AVT for Speech Communication

Complete methodology and PyTorch implementation of **Multi-Resolution Audio--Visual Transformer with Heterogeneous Graph Fusion for Robust Speech Emotion Recognition**.

> **If GitHub shows only a one-line README:** you are on `main`. Open
> [pull request #1](https://github.com/Ammaramjad/SpeechCommunicatuion/pull/1)
> or switch the branch dropdown to `cursor/mr-avt-complete-methodology-code-0dda`.

## Bundled data (no download required)

Licensed corpora (AFEW5.0, BAUM-1s, IEMOCAP) **cannot** be placed in this repository.
A **demo set is committed** at `data/demo/` (48 WAV + NPY clips, `manifest.csv`).

```bash
pip install -r requirements.txt
python train.py --config configs/demo.yaml --manifest data/demo/manifest.csv --device cpu
```

Defaults are already the demo config and demo manifest, so `python train.py` is enough.

## Layout

- `data/demo/` — runnable audio–visual clips and `manifest.csv`
- `docs/METHODOLOGY.md` — full method (all modules and losses)
- `paper/method_section.tex` — Speech Communication method section
- `mr_avt/` — model, losses, training, robustness evaluation
- `configs/demo.yaml` — small model matching the demo clips
- `configs/default.yaml` — paper-sized hyperparameters

## Paper datasets

Download AFEW / BAUM-1s / IEMOCAP from their providers, then write a CSV:

```text
audio,video,label,speaker,session,split
```

```bash
python train.py --config configs/default.yaml --manifest path/to/iemocap.csv --device cuda
```

## Tests

```bash
python -m pytest tests -q
```
