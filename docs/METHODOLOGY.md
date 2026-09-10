# Complete Methodology: Multi-Resolution Audio--Visual Transformer (MR-AVT)

This document is the implementation-complete methodology for the Speech Communication manuscript
*Multi-Resolution Audio--Visual Transformer with Heterogeneous Graph Fusion for Robust Speech Emotion Recognition*.
It restates every module with the exact tensors, losses, and algorithms used in `mr_avt/`.

## 1. Problem formulation

An utterance is the pair \(X=\{X^{a},X^{v}\}\), where \(X^{a}\) is a 16 kHz mono waveform and \(X^{v}\) is a synchronized facial video. The model \(f_{\theta}\) predicts a discrete emotion \(y\in\mathcal{Y}\):

\[
\hat y = f_{\theta}(X)=\mathcal{H}_{\theta}\big(\Phi^{a}_{MR}(X^{a}),\Phi^{v}(X^{v})\big).
\]

Five stages are composed in order:

1. Multi-resolution audio encoding (short / mid / long transformers).
2. Visual encoding (per-frame ViT + temporal EMA).
3. Heterogeneous audio--visual graph refinement.
4. Uncertainty-aware fusion.
5. Pre-gated selection of audio temporal branches at inference.

## 2. Audio front-end

Waveforms are peak-trimmed/padded to at most \(T_{\max}\) seconds (default 8 s). Three log-Mel spectrograms with 64 bins are computed at 16 kHz:

| Branch | Window | Hop | FFT | Physical window |
|--------|--------|-----|-----|-----------------|
| short \(s\) | 400 | 160 | 512 | 25 ms / 10 ms |
| mid \(m\) | 1600 | 400 | 2048 | 100 ms / 25 ms |
| long \(\ell\) | 8000 | 1600 | 8192 | 500 ms / 100 ms |

\[
S_{r}=\mathrm{MelSpec}(X^{a};w_{r},h_{r}),\qquad
\bar S_{r}=(S_{r}-\mu_{r})/(\sigma_{r}+\epsilon).
\]

Each spectrogram is truncated or zero-padded to \(T=80\) frames (paper setting; tests use 16). Per-resolution instance normalization is applied inside each branch before the linear projection.

## 3. Resolution-specific transformers

For branch \(r\in\{s,m,\ell\}\):

\[
E_{r}=W_{r}\bar S_{r}+b_{r},\qquad
Z_{r}^{0}=E_{r}+\mathrm{PE}_{r},\qquad
H_{r}^{a}=\mathrm{Transformer}(Z_{r}^{0}).
\]

Default transformer: 6 layers, 8 heads, \(d=768\), FFN 3072, GELU, dropout 0.1, pre-norm. Padding tokens are masked in self-attention.

## 4. Cross-resolution interaction

Token sequences have different lengths, so interaction is defined on pooled branch summaries

\[
u_{r}=P_{r}(\mathrm{Pool}(H_{r}^{a}))\in\mathbb{R}^{d}.
\]

Compatibility and residual mixing:

\[
\omega_{ij}=\frac{\exp(u_{i}^{\top}u_{j}/\sqrt{d})}{\sum_{k}\exp(u_{i}^{\top}u_{k}/\sqrt{d})},\qquad
\hat u_{i}=u_{i}+\sum_{j\neq i}\omega_{ij}u_{j}.
\]

Alignment loss in the shared space:

\[
\mathcal{L}_{\mathrm{align}}=\sum_{i\neq j}\beta_{ij}\big\|P_{ij}(\hat u_{i})-\hat u_{j}\big\|_{2}^{2}.
\]

Utterance-level audio summary before the graph:

\[
\alpha_{r}=\frac{\exp(q^{\top}\hat u_{r})}{\sum_{k}\exp(q^{\top}\hat u_{k})},\qquad
Z^{a}=\sum_{r}\alpha_{r}\hat u_{r}.
\]

The token sequences \(H_{r}^{a}\) are retained for graph nodes.

## 5. Visual encoder

Sixteen uniformly sampled RGB frames are resized to \(224\times 224\). Each frame is encoded by a ViT-B/16-style encoder (patch 16, CLS token). Temporal EMA smoothing

\[
\tilde H_{t}^{v}=\eta H_{t}^{v}+(1-\eta)H_{t-1}^{v},\qquad \eta=0.1
\]

is applied along time. Global pooled \(Z^{v}=\mathrm{Pool}(\tilde H_{1:N}^{v})\) is the utterance visual vector; frame tokens \(\tilde H_{t}^{v}\) become visual graph nodes.

In this repository the ViT weights are trained from scratch unless `use_pretrained_vit` is enabled. The manuscript uses ImageNet-21k pretraining followed by ImageNet-1k fine-tuning of ViT-B/16.

## 6. Heterogeneous graph

Nodes:

\[
v^{a}_{r,t}=P_{a}(H^{a}_{r,t}),\qquad v^{v}_{t}=P_{v}(\tilde H^{v}_{t}).
\]

Audio tokens are stride-subsampled to at most \(K_{g}=32\) frames per resolution so that message passing stays \(\mathcal{O}(|E|d)\).

Edges:

- temporal: adjacent tokens within each resolution and within the visual stream;
- semantic: \(k=8\) nearest neighbors under Gaussian affinity \(A_{ij}=\exp(-\|z_{i}-z_{j}\|_{2}^{2}/\tau_{g})\), \(\tau_{g}=0.5\).

Learned GAT (2 layers, 8 heads, ELU) is applied only on the sparse neighborhood:

\[
\alpha_{ij}=\mathrm{softmax}_{j\in\mathcal{N}(i)}\mathrm{LeakyReLU}\big(a^{\top}[Wh_{i}\|Wh_{j}]\big),\qquad
h_{i}'=\sigma\Big(\sum_{j}\alpha_{ij}Wh_{j}\Big),\qquad
\hat h_{i}=h_{i}+h_{i}'.
\]

Pooled graph outputs \(\tilde Z^{a},\tilde Z^{v}\) feed fusion.

### Cross-modal consistency (completed definition)

The manuscript refers to \(\mathcal{L}_{\mathrm{cm}}\) in the graph module without an expanded formula. The implementation uses cosine consistency of projected graph embeddings:

\[
\mathcal{L}_{\mathrm{cm}}=1-\cos\big(P_{\mathrm{cm}}^{a}(\tilde Z^{a}),P_{\mathrm{cm}}^{v}(\tilde Z^{v})\big).
\]

This penalizes disagreement between refined audio and visual utterance vectors without requiring equal-length token sequences.

## 7. Uncertainty-aware fusion

\[
\sigma_{m}^{2}=\mathrm{Softplus}(g_{m}(F_{m})),\qquad
\rho_{m}=\exp(-\sigma_{m}^{2}),\qquad
w_{m}=\frac{\rho_{m}}{\rho_{a}+\rho_{v}},\qquad
F=w_{a}F_{a}+w_{v}F_{v}.
\]

\(\sigma_{m}^{2}\) is a learned reliability proxy, not a calibrated Bayesian variance. Missing-modality evaluation zeroes the dropped stream and its nodes so that \(w_{m}\) can collapse onto the remaining modality.

## 8. Pre-gated multi-resolution computation

A lightweight CNN preview \(F_{0}\) is computed from the *short* Mel spectrogram *before* the full branch transformers (in batched training all branches still run so that every encoder receives gradients). Branch logits \(s=W_{g}F_{0}+b_{g}\in\mathbb{R}^{3}\) yield

\[
\gamma_{r}=\mathrm{softmax}(s)_{r}.
\]

A branch is executed at inference if \(\gamma_{r}>\delta\) with \(\delta=0.5\). Because \(\sum_{r}\gamma_{r}=1\), at most one branch can exceed 0.5; otherwise the argmax branch is kept. This is a dominant-branch rule with fallback, not simultaneous multi-branch execution.

Gate training uses only training labels. For each sample the branch classifier with smallest cross-entropy is the target \(r^{*}(x)\):

\[
\mathcal{L}_{\mathrm{gate}}=-\log p_{g}(r^{*}(x)\mid F_{0}).
\]

Held-out data never enter gate targets.

## 9. Joint objective

\[
\mathcal{L}=\lambda_{1}\mathcal{L}_{\mathrm{cls}}+\lambda_{2}\mathcal{L}_{\mathrm{con}}+\lambda_{3}\mathcal{L}_{\mathrm{aug}}+\lambda_{4}\mathcal{L}_{\mathrm{cm}}+\lambda_{5}\mathcal{L}_{\mathrm{align}}+\lambda_{6}\mathcal{L}_{\mathrm{gate}}
\]

with \((\lambda_{1},\ldots,\lambda_{6})=(1.0,0.5,0.5,0.1,0.1,0.05)\).

- \(\mathcal{L}_{\mathrm{cls}}\): categorical cross-entropy on the fused head.
- \(\mathcal{L}_{\mathrm{con}}\): supervised contrastive loss on fused embeddings, \(\tau_{c}=0.07\).
- \(\mathcal{L}_{\mathrm{aug}}\): RBF-kernel MMD between clean fused embeddings and embeddings of a training-set perturbation (additive Gaussian noise). This is a source-side consistency regularizer, not target-domain adaptation.
- \(\mathcal{L}_{\mathrm{cm}}\), \(\mathcal{L}_{\mathrm{align}}\), \(\mathcal{L}_{\mathrm{gate}}\): as above.

Optimizer: AdamW, \(\mathrm{lr}=10^{-4}\), weight decay \(0.01\), cosine decay, 10% linear warm-up, batch 32, max 100 epochs, early stopping patience 10, gradient clip 1.0.

## 10. Evaluation protocols (do not mix)

| Corpus | Protocol | Metric | Label space |
|--------|----------|--------|-------------|
| AFEW5.0 | Official EmotiW split; report **validation** (test labels unavailable) | Accuracy | 7 classes |
| BAUM-1s | 5-fold leave-one-subject-group-out, 521 clips / 31 speakers | Accuracy | 6 classes |
| IEMOCAP | 5-fold leave-one-session-out; excited merged into happy; 5531 utterances | Weighted accuracy | 4 classes |

Robustness is evaluation-only on the held-out split:

- Gaussian SNR \(\in\{20,10,5,0\}\) dB
- visual frame dropout \(\in\{0,25,50,75\}\%\)
- missing audio or missing visual
- imbalance: audio at 5 dB **or** visual 50% dropout
- babble / traffic / pink at 5 dB; reverberation \(T_{60}=0.6\) s

## 11. Complexity

Transformer branch \(r\): \(\mathcal{O}(N_{r}^{2}d)\). Sparse GAT: \(\mathcal{O}(|E|d)\). Fusion: \(\mathcal{O}(d)\). Adaptive inference cost is the sum of executed branches only. This repository reports analytical activation masks; it does not claim measured hardware latency.

## 12. Mapping from equations to code

| Module | File |
|--------|------|
| Mel spectrograms + transformers + cross-resolution | `mr_avt/models/audio.py` |
| ViT + EMA smoothing | `mr_avt/models/visual.py` |
| Graph + \(\mathcal{L}_{\mathrm{cm}}\) | `mr_avt/models/graph.py` |
| Uncertainty fusion + branch gate | `mr_avt/models/fusion.py` |
| Full forward | `mr_avt/models/mr_avt.py` |
| Losses | `mr_avt/models/losses.py` |
| Train / eval / robustness | `mr_avt/engine.py` |
| Manifest datasets | `mr_avt/data/datasets.py` |
| Paper hyperparameters | `configs/default.yaml` |
