from pathlib import Path

from torch.utils.data import DataLoader

from mr_avt.config import MRAVTConfig
from mr_avt.data.datasets import ManifestDataset, collate_batch, load_manifest


def test_bundled_demo_manifest_is_nonempty():
    manifest = Path("data/demo/manifest.csv")
    assert manifest.exists(), "data/demo/manifest.csv must be committed in the repo"
    samples = load_manifest(manifest)
    assert len(samples) >= 16
    assert any(s.split == "train" for s in samples)
    assert any(s.split == "val" for s in samples)
    wav_files = list(Path("data/demo/audio").glob("*.wav"))
    npy_files = list(Path("data/demo/video").glob("*.npy"))
    assert len(wav_files) >= 16
    assert len(npy_files) >= 16


def test_demo_loader_returns_nonzero_audio():
    cfg = MRAVTConfig.from_yaml("configs/demo.yaml")
    samples = [s for s in load_manifest("data/demo/manifest.csv") if s.split == "train"][:4]
    ds = ManifestDataset(
        samples,
        sample_rate=cfg.sample_rate,
        max_audio_seconds=cfg.max_audio_seconds,
        num_visual_frames=cfg.num_visual_frames,
        image_size=cfg.image_size,
    )
    batch = collate_batch([ds[i] for i in range(len(ds))])
    assert batch["waveform"].abs().sum() > 0
    assert batch["frames"].shape[0] == len(ds)
    assert batch["frames"].shape[1] == cfg.num_visual_frames
    loader = DataLoader(ds, batch_size=2, collate_fn=collate_batch)
    first = next(iter(loader))
    assert first["label"].numel() == 2
