# Official fold construction

IEMOCAP and SAVEE are licensed corpora and are **not** redistributed.

```bash
python scripts/build_official_splits.py \
  --iemocap /path/to/IEMOCAP \
  --savee /path/to/SAVEE \
  --out splits/
```

The JSON files in this directory already encode the **protocol** used in the paper
(5-fold LOSO sessions Ses01–Ses05; 4-fold SAVEE speakers DC/JE/JK/KL). The builder
writes per-utterance `train` / `val` / `test` ID lists once the licensed files are present.
