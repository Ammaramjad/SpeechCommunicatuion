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
