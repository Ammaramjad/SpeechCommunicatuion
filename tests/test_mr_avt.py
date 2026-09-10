from __future__ import annotations

import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mr_avt.config import MRAVTConfig
from mr_avt.data.corruptions import add_gaussian_noise, visual_frame_dropout
from mr_avt.models.fusion import BranchGate
from mr_avt.models.losses import MRAVTCriterion
from mr_avt.models.mr_avt import MRAVT


def _batch(cfg: MRAVTConfig, bsz: int = 4):
    sr = cfg.sample_rate
    samples = int(sr * 0.4)
    waveform = torch.randn(bsz, samples)
    frames = torch.rand(bsz, cfg.num_visual_frames, 3, cfg.image_size, cfg.image_size)
    labels = torch.randint(0, cfg.num_classes, (bsz,))
    frame_mask = torch.ones(bsz, cfg.num_visual_frames, dtype=torch.bool)
    return waveform, frames, labels, frame_mask


def test_forward_and_backward_shapes():
    cfg = MRAVTConfig.tiny(num_classes=4)
    model = MRAVT(cfg)
    criterion = MRAVTCriterion(
        cfg.num_classes,
        cfg.model.dim,
        cfg.model.contrastive_tau,
        {"cls": 1, "con": 0.5, "aug": 0.5, "cm": 0.1, "align": 0.1, "gate": 0.05},
    )
    waveform, frames, labels, frame_mask = _batch(cfg)
    out = model(waveform, frames, frame_mask=frame_mask)
    assert out["fused"].shape == (4, cfg.model.dim)
    assert out["gate_logits"].shape == (4, 3)
    assert set(out["branch_summaries"]) == {"s", "m", "l"}
    losses = criterion(
        out["fused"],
        labels,
        out["branch_summaries"],
        out["gate_logits"],
        out["align_loss"],
        out["cm_loss"],
        fused_aug=out["fused"],
    )
    losses["loss"].backward()
    grads = [p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters() if p.requires_grad]
    assert any(grads)
    assert torch.isfinite(losses["loss"])


def test_gate_argmax_fallback():
    logits = torch.tensor([[0.2, 0.3, 0.1], [2.0, 0.1, 0.1]])
    active = BranchGate.select_branches(logits, delta=0.5)
    assert active.shape == (2, 3)
    assert int(active[0].sum().item()) == 1
    assert bool(active[1, 0].item()) is True
    assert active.any(dim=-1).all()


def test_missing_modality_zeroes_stream():
    cfg = MRAVTConfig.tiny()
    model = MRAVT(cfg).eval()
    waveform, frames, _, frame_mask = _batch(cfg, bsz=2)
    audio_off = torch.tensor([0.0, 1.0])
    visual_off = torch.tensor([1.0, 0.0])
    out = model(
        waveform,
        frames,
        frame_mask=frame_mask,
        audio_mask_mod=audio_off,
        visual_mask_mod=visual_off,
    )
    assert torch.allclose(out["z_audio"][0], torch.zeros_like(out["z_audio"][0]))
    assert torch.allclose(out["z_visual"][1], torch.zeros_like(out["z_visual"][1]))
    assert out["fusion_weights"].sum(dim=-1).allclose(torch.ones(2), atol=1e-5)


def test_adaptive_inference_keeps_one_branch():
    cfg = MRAVTConfig.tiny()
    model = MRAVT(cfg).eval()
    waveform, frames, _, frame_mask = _batch(cfg, bsz=3)
    out = model(waveform, frames, frame_mask=frame_mask, adaptive=True)
    assert out["active_branches"].any(dim=-1).all()
    assert out["active_branches"].sum(dim=-1).max() <= 3


def test_corruptions_preserve_shape():
    wav = torch.randn(2, 8000)
    frames = torch.rand(2, 4, 3, 32, 32)
    noisy = add_gaussian_noise(wav, 5.0)
    dropped, mask = visual_frame_dropout(frames, 0.5)
    assert noisy.shape == wav.shape
    assert dropped.shape == frames.shape
    assert mask.shape == (2, 4)


def test_spectrograms_three_resolutions():
    cfg = MRAVTConfig.tiny()
    model = MRAVT(cfg)
    wav = torch.randn(2, int(cfg.sample_rate * 0.4))
    specs, masks = model.spectrograms(wav)
    assert set(specs) == {"s", "m", "l"}
    for name in specs:
        assert specs[name].shape[0] == 2
        assert specs[name].shape[1] == cfg.n_mels
        assert specs[name].shape[2] == cfg.temporal_frames
        assert masks[name].shape == (2, cfg.temporal_frames)
