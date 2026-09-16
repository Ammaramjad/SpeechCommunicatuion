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
