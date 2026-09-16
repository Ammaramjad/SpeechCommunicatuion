# Regenerated manuscript tables

Source: `/workspace/results/paper/tables.json`

## table2_sync

| Condition | Acc. (%) | Δ vs aligned |
| --- | --- | --- |
| Aligned, linear interpolation (default) | 86.7 | -- |
| Aligned, nearest-neighbour resampling | 86.5 | -0.2 |
| Video shifted ±33 ms | 86.4 | -0.3 |
| Video shifted ±100 ms | 85.6 | -1.1 |
| Video shifted ±200 ms | 83.9 | -2.8 |

## table3_pca

| K | Retained var. (%) | Text-only | A+V+T |
| --- | --- | --- | --- |
| 12 | 71.4 | 81.5 | 86.7 |
| 32 | 84.9 | 81.9 | 86.8 |
| 64 | 91.7 | 82.1 | 86.9 |
| 128 | 96.2 | 82.3 | 87.0 |
| 768 | 100.0 | 82.4 | 87.1 |

## table4_fusion

| Fusion operator | WA (%) | Params | Train time (rel.) |
| --- | --- | --- | --- |
| Concatenation (proposed) | 86.7±1.3 | 1,214k | 1.00 |
| Cross-modal attention (audio query) | 86.1±1.5 | 1,676k | 1.41 |
| Tensor fusion (low-rank, r=16) | 85.8±1.6 | 1,979k | 1.63 |
| Late (decision-level) fusion | 84.9±1.4 | 1,275k | 1.05 |

## table5_capacity

| Configuration | Train Acc. | Val. Acc. | Test Acc. | Params |
| --- | --- | --- | --- | --- |
| 1 layer, 128 units | 91.2 | 85.1 | 84.9 | 1.1M |
| 2 layers, 64 units | 90.4 | 85.3 | 85.2 | 0.6M |
| 2 layers, 128 units (EHOLF) | 93.1 | 86.9 | 86.7 | 1.2M |
| 2 layers, 192 units | 95.6 | 86.0 | 85.8 | 1.9M |
| 2 layers, 256 units | 97.8 | 84.9 | 84.6 | 2.6M |
| 3 layers, 128 units | 94.9 | 85.7 | 85.4 | 1.3M |

## table6_eholf

| Hyperparameter | IEMOCAP | SAVEE |
| --- | --- | --- |
| Initial learning rate θ1 | 2.3e-3 (1e-4--1e-2) | 3.1e-3 (1e-4--1e-2) |
| L2 factor θ2 | 4.7e-4 (1e-5--1e-2) | 8.2e-4 (1e-5--1e-2) |
| Dropout rate θ3 | 0.32 (0.1--0.5) | 0.38 (0.1--0.5) |
| LSTM hidden units θ4 | 128 (64--256) | 128 (64--256) |
| LSTM layers (fixed) | 2 | 2 |
| Batch size (fixed) | 32 | 16 |
| Max. epochs / patience | 100 / 10 | 100 / 10 |
| Optimizer / LR schedule | Adam / cosine annealing | Adam / cosine annealing |
| EHOLF population N / Tmax | 30 / 100 | 30 / 100 |
| Lévy β; AW | 1.5; 0.3, 0.9, 2.0 | 1.5; 0.3, 0.9, 2.0 |
| PCA components K | 12 | None |
| Random seeds | 0-4 | 0-4 |

## table7_compute

| Phase | Per utterance | IEMOCAP total | SAVEE total | Pipeline share (%) |
| --- | --- | --- | --- | --- |
| BERT text features | 18 ms | 0.3 h | -- | 3 |
| ResNet-50 + landmarks (video) | 62 ms | 1.9 h | 0.2 h | 17 |
| MFCC + spectral (audio) | 6 ms | 0.1 h | 0.1 h | 1 |
| EHOLF search (N=30, until convergence) | -- | 4.6 h | 2.1 h | 42 |
| Final LSTM training | -- | 3.2 h | 1.8 h | 29 |
| Kernel SHAP (200 utterances/fold) | 4.2 s | 0.9 h | 0.4 h | 8 |
| LSTM inference (features cached) | 15 ms | -- | -- | -- |
| End-to-end inference (including features) | 101 ms | -- | -- | -- |

## table8_folds

### IEMOCAP
| Fold | WA | UA | Macro-F1 | Precision | AUC (micro) |
| --- | --- | --- | --- | --- | --- |
| Ses01 | 87.9 | 86.5 | 87.6 | 87.8 | 0.96 |
| Ses02 | 85.4 | 83.8 | 85.0 | 85.3 | 0.94 |
| Ses03 | 86.1 | 84.6 | 85.8 | 86.0 | 0.95 |
| Ses04 | 88.2 | 86.9 | 87.9 | 88.1 | 0.96 |
| Ses05 | 85.9 | 84.2 | 85.7 | 85.8 | 0.94 |
| Mean ± SD | 86.7 ± 1.3 | 85.2 ± 1.4 | 86.4 ± 1.3 | 86.6 ± 1.3 | 0.95 ± 0.01 |

### SAVEE
| Fold | WA | UA | Macro-F1 | Precision | AUC (micro) |
| --- | --- | --- | --- | --- | --- |
| DC | 93.3 | 92.9 | 93.1 | 93.2 | 0.98 |
| JE | 90.4 | 89.8 | 90.0 | 90.3 | 0.96 |
| JK | 92.9 | 92.5 | 92.6 | 92.8 | 0.97 |
| KL | 91.8 | 91.2 | 91.5 | 91.7 | 0.97 |
| Mean ± SD | 92.1 ± 1.3 | 91.6 ± 1.4 | 91.8 ± 1.4 | 92.0 ± 1.3 | 0.97 ± 0.01 |

## table9_ablation

| Variant | Accuracy (%) | Convergence iterations |
| --- | --- | --- |
| ARO (baseline) | 82.9 | 74 |
| ARO + LF | 84.3 | 58 |
| ARO + AIW | 83.8 | 61 |
| LSTM-EHOLF (LF + AIW) | 86.7 | 43 |

## table10_baselines

### IEMOCAP
| Metric | RNN | GRU | GAN | TNN | LSTM-EHOLF |
| --- | --- | --- | --- | --- | --- |
| Accuracy (%) | 78.4±1.8 | 82.6±1.5 | 80.3±2.1 | 85.4±1.4 | 86.7±1.3 |
| UA (%) | 76.5±1.9 | 80.9±1.6 | 78.4±2.2 | 83.7±1.5 | 85.2±1.4 |
| F1 Score (%) | 77.9±1.9 | 82.1±1.6 | 79.8±2.2 | 85.0±1.5 | 86.4±1.3 |
| Precision (%) | 78.1±1.8 | 82.4±1.5 | 80.1±2.1 | 85.2±1.4 | 86.6±1.3 |

### SAVEE
| Metric | RNN | GRU | GAN | TNN | LSTM-EHOLF |
| --- | --- | --- | --- | --- | --- |
| Accuracy (%) | 86.4±2.0 | 88.7±1.7 | 87.3±2.3 | 90.8±1.6 | 92.1±1.3 |
| UA (%) | 85.7±2.1 | 88.0±1.8 | 86.5±2.4 | 90.1±1.7 | 91.6±1.4 |
| F1 Score (%) | 85.9±2.1 | 88.2±1.8 | 86.7±2.4 | 90.2±1.7 | 91.8±1.4 |
| Precision (%) | 86.1±2.0 | 88.4±1.7 | 87.0±2.3 | 90.5±1.6 | 92.0±1.3 |

## table11_dropout

| Configuration | IEMOCAP (%) | SAVEE (%) |
| --- | --- | --- |
| Audio only (A) | 79.1 | 87.3 |
| Video only (V) | 77.4 | 86.2 |
| Text only (T) | 81.5 | -- |
| Audio + Video (A+V) | 83.9 | 90.4 |
| Audio + Text (A+T) | 84.8 | -- |
| Video + Text (V+T) | 83.2 | -- |
| A+V+T (full) | 86.7 | 92.1 |

## table12_noise

| Degradation | IEMOCAP | SAVEE | TNN IEMOCAP | TNN SAVEE |
| --- | --- | --- | --- | --- |
| Clean (no noise) | 86.7 | 92.1 | 85.4 | 90.8 |
| Audio noise, 20 dB SNR | 84.3 | 90.5 | 82.5 | 88.6 |
| Audio noise, 10 dB SNR | 81.2 | 88.4 | 78.7 | 85.9 |
| Audio noise, 0 dB SNR | 75.6 | 84.0 | 71.8 | 80.4 |
| Video blur, sigma=1.0 | 84.9 | 90.9 | 82.9 | 88.8 |
| Video blur, sigma=2.0 | 80.7 | 87.6 | 78.1 | 84.7 |
| Joint, mild (20 dB + sigma=1.0) | 82.6 | 89.2 | 80.3 | 86.9 |
| Joint, moderate (10 dB + sigma=1.0) | 78.9 | 86.1 | 75.4 | 82.8 |
| Joint, severe (0 dB + sigma=2.0) | 71.8 | 80.9 | 66.2 | 75.3 |
| Joint, severe + 20% text-token corruption | 69.4 | -- | 63.1 | -- |

## table13_cross

| Train → Test | Setting | Accuracy (%) |
| --- | --- | --- |
| IEMOCAP4 -> IEMOCAP4 | In-domain | 86.7 |
| SAVEE4 -> SAVEE4 | In-domain | 94.2 |
| IEMOCAP4 -> SAVEE4 | Cross-domain | 58.6 |
| SAVEE4 -> IEMOCAP4 | Cross-domain | 54.1 |
| Chance (uniform, 4 classes) | Reference | 25.0 |
| Majority class, SAVEE4 target | Reference | 40.0 |
| Majority class, IEMOCAP4 target | Reference | 40.2 |
| Audio-only LSTM, IEMOCAP4 -> SAVEE4 | Cross-domain baseline | 51.3 |
| Audio-only LSTM, SAVEE4 -> IEMOCAP4 | Cross-domain baseline | 47.8 |

## table14_shap

| Feature category | Specific features | Mean SHAP | Dominant emotion(s) | Interpretation |
| --- | --- | --- | --- | --- |
| Audio Features | MFCC 1-5, Spectral Flux | 0.312 | Angry | Strong acoustic contribution to angry predictions |
| Visual Features | Eyebrow Curvature, Lip Movement | 0.241 | Happy | Strong facial contribution to happy predictions |
| Textual Features | PCA-reduced BERT latent components | 0.294 | Sad, Neutral | Strong contribution of the latent textual representation to sad and neutral predictions |

## table15_shap

| Emotion | Audio (%) | Visual (%) | Textual (%) |
| --- | --- | --- | --- |
| Angry | 38.6 | 26.8 | 34.6 |
| Happy | 29.3 | 42.1 | 28.6 |
| Sad | 22.6 | 27.6 | 49.8 |
| Neutral | 19.3 | 25.4 | 55.3 |

## table16_shap

| Source of variation | SD audio | SD visual | SD text | Max. SD (class) | ρ | Dominant preserved (%) |
| --- | --- | --- | --- | --- | --- | --- |
| (a) 5 LOSO folds | 1.6 | 1.2 | 1.8 | 1.8 (sad) | 0.94 | 96 |
| (b) 5 seeds, fixed fold | 0.9 | 0.7 | 1.1 | 1.1 (sad) | 0.97 | 100 |
| (c) 1,000 bootstraps, fixed model | 0.6 | 0.5 | 0.7 | 0.7 (sad) | 0.98 | 100 |

## table17_matched

### IEMOCAP
| Method | Mod. | Cls. | Protocol | Acc./WA (%) | UA (%) |
| --- | --- | --- | --- | --- | --- |
| Early-fusion BiLSTM (our re-implementation) | A+V+T | 4 | IEMOCAP, 5-fold LOSO | 83.9±1.6 | 82.3±1.7 |
| MulT (re-run) | A+V+T | 4 | IEMOCAP, 5-fold LOSO | 85.2±1.5 | 83.6±1.6 |
| MISA (re-run) | A+V+T | 4 | IEMOCAP, 5-fold LOSO | 84.6±1.7 | 83.0±1.8 |
| TNN | A+V+T | 4 | IEMOCAP, 5-fold LOSO | 85.4±1.4 | 83.7±1.5 |
| LSTM-EHOLF (Proposed) | A+V+T | 4 | IEMOCAP, 5-fold LOSO | 86.7±1.3 | 85.2±1.4 |

### SAVEE
| Method | Mod. | Cls. | Protocol | Acc./WA (%) | UA (%) |
| --- | --- | --- | --- | --- | --- |
| Early-fusion BiLSTM (our re-implementation) | A+V | 7 | SAVEE, 4-fold speaker-independent | 89.7±1.9 | 89.1±2.0 |
| TNN | A+V | 7 | SAVEE, 4-fold speaker-independent | 90.8±1.6 | 90.1±1.7 |
| LSTM-EHOLF (Proposed) | A+V | 7 | SAVEE, 4-fold speaker-independent | 92.1±1.3 | 91.6±1.4 |

