# LSTM-EHOLF methodology (implementation-complete)

This document is the executable counterpart of Section 3 of
*Explainable and Noise-Robust Multimodal Emotion Recognition Using LSTM-EHOLF*.
Every equation below is implemented in `preprocessing/`, `eholf/`, `lstm_eholf/`, `explain/`, and `robustness/`.

## 1. Corpora and protocol

- **IEMOCAP**: four classes `{neutral, sad, happy, angry}`, modalities **A+V+T**, **5-fold leave-one-session-out** (`splits/iemocap_loso.json`).
- **SAVEE**: seven classes, modalities **A+V only** (scripted text is excluded), **4-fold speaker-independent** (`splits/savee_speaker.json`).
- Per-fold z-score statistics, BERT PCA, and EHOLF fitness use **training (+ inner validation) only**. The held-out session/speaker is touched once, after search terminates.

Class counts (Table 1) are stored in the split JSON files.

## 2. Features

### Audio (78-D)

25 ms Hamming window, 10 ms hop. Per frame: 13 MFCC + Δ + ΔΔ (39) plus spectral centroid, roll-off and flux. Utterance pooling: mean and std of the 39 MFCC-family coefficients → \(\mathbf{F}_a\in\mathbb{R}^{78}\) (`preprocessing/audio.py`).

Noise protocol: \(s_{\mathrm{noisy}}=s+n\) with \(n\sim\mathcal{N}(0,\sigma^2)\) scaled to SNR \(\in\{20,10,0\}\) dB.

### Video

ResNet-50 + HFGP/LFGP deep embedding \(\in\mathbb{R}^{2048}\) concatenated with 8 geometric descriptors from 68 Dlib landmarks (`preprocessing/video.py`):

1. Rigid Procrustes alignment on eye corners, nose bridge, chin.
2. Scale-normalize distances by inter-ocular distance.
3. Subject-relative baseline: median of the speaker’s neutral training frames, or the first 15 frames of a held-out test utterance (no labels).

Video blur: Gaussian \(\sigma\in\{1.0,2.0\}\).

### Text

BERT-base `[CLS]` \(\in\mathbb{R}^{768}\), then **per-fold PCA** with \(K=12\) (71.4% variance on IEMOCAP training `[CLS]`). SHAP is applied to the 12 latent components, not to tokens.

## 3. Alignment and fusion

Audio 10 ms grid is the reference timeline. Video is piecewise-linearly interpolated (nearest-neighbour ablation in Table 2). Text is a single utterance vector — never interpolated onto frames.

\[
\mathbf{F}^{(u)}_{\mathrm{IEMOCAP}} = [\mathbf{F}_a^{(u)}\Vert\mathbf{F}_v^{(u)}\Vert\mathbf{F}_t^{(u)}],\qquad
\mathbf{F}^{(u)}_{\mathrm{SAVEE}} = [\mathbf{F}_a^{(u)}\Vert\mathbf{F}_v^{(u)}].
\]

LSTM sequences are chronological utterance vectors **within a dialogue**; they never cross session boundaries. Fusion operators in Table 4: concatenation (proposed), audio-query cross-modal attention, low-rank tensor fusion \(r=16\), late fusion (`lstm_eholf/fusion.py`, `lstm_eholf/models.py`).

## 4. LSTM + training

2-layer LSTM, hidden size searched in \([64,256]\) (EHOLF selected 128). Adam, cosine annealing, early stopping patience 10, class-weighted CE with \(\sum_c w_c=C\), class-balanced sampler (no SMOTE).

Metrics: WA, UA, macro-F1, macro-precision, micro AUC (`lstm_eholf/metrics.py`). Fold SD uses \(n-1\).

## 5. EHOLF (`eholf/optimizer.py`)

Search \(\theta=(\mathrm{lr}, L_2, \mathrm{dropout}, h)\) with \(f(\theta)=1-\mathrm{Acc}_{val}(\theta)\).

Lévy step (Mantegna, \(\beta=1.5\)):

\[
s=\frac{u}{|v|^{1/\beta}},\quad
\sigma_u=\Big[\frac{\Gamma(1+\beta)\sin(\pi\beta/2)}{\Gamma((1+\beta)/2)\,\beta\,2^{(\beta-1)/2}}\Big]^{1/\beta}.
\]

If \(\mathrm{rand}<0.6\): exploration \(\theta \leftarrow \theta + s(\theta-\theta_k)+s(\theta^*-\theta)\).
Else: exploitation with adaptive inertia \(AW(t)=AW_{\min}+(AW_{\max}-AW_{\min})e^{-\gamma t/T_{\max}}\).

Variants for Table 9: ARO, ARO+LF, ARO+AIW, EHOLF.

## 6. Kernel SHAP (`explain/kernel_shap.py`)

Explains softmax probabilities, 2048 coalitions, 100 k-means background training utterances, 200 test utterances/fold. Modality importance is \(\sum_{i\in\mathcal{S}_m}|\phi_i|\) normalized per class. Stability: folds, seeds, 1000 bootstraps (Table 16).

## 7. Robustness

- Dropout of A/V/T and bimodal subsets (Table 11).
- Audio AWGN, video blur, joint corruption, 20% text-token corruption (Table 12).
- Four-class IEMOCAP\(\leftrightarrow\)SAVEE with no target fine-tuning (Table 13).

## 8. What cloning this repository reproduces

| Artefact | Command |
|---|---|
| Tables 2–17 | `python tables/make_tables.py` |
| Figs. 3–7 | `python figures/make_figures.py` |
| Synthetic end-to-end (no licensed data) | `python reproduce.py --demo` |
| Official splits | `python scripts/build_official_splits.py --iemocap DIR --savee DIR` |

IEMOCAP/SAVEE media **cannot** be shipped. `results/paper/*.json` are the **derived logs** from which every published number and figure is generated. Retraining on the licensed corpora uses `configs/iemocap.yaml` and `configs/savee.yaml` after splits are materialized.
