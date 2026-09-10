# Data

This repository includes a **bundled demo corpus** under `data/demo/` so training
and evaluation run without downloading anything.

| Path | Contents |
|------|----------|
| `data/demo/manifest.csv` | 48 clips (32 train / 16 val), 4 synthetic emotion classes |
| `data/demo/audio/*.wav` | 16 kHz mono tones (1 s) |
| `data/demo/video/*.npy` | 8 RGB frames of size 32×32 |

This demo is **not** AFEW5.0, BAUM-1s, or IEMOCAP. Those corpora are licensed and
cannot be redistributed here. To run the paper protocol, download them from the
original providers and write a manifest with columns:

```text
audio,video,label,speaker,session,split
```

Then point training at that file:

```bash
python train.py --config configs/default.yaml --manifest path/to/manifest.csv
```
