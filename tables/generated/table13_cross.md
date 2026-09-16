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
