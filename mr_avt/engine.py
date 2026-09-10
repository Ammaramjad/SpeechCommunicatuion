"""Training and evaluation entry points for MR-AVT."""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from mr_avt.config import MRAVTConfig
from mr_avt.data.corruptions import add_colored_noise, add_gaussian_noise, apply_reverb, visual_frame_dropout
from mr_avt.data.datasets import ManifestDataset, collate_batch, filter_split, load_manifest
from mr_avt.models.losses import MRAVTCriterion
from mr_avt.models.mr_avt import MRAVT


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def cosine_warmup_lambda(step: int, warmup: int, total: int) -> float:
    if step < warmup:
        return float(step + 1) / float(max(1, warmup))
    progress = (step - warmup) / float(max(1, total - warmup))
    return 0.5 * (1.0 + math.cos(math.pi * progress))


@torch.no_grad()
def evaluate(
    model: MRAVT,
    criterion: MRAVTCriterion,
    loader: DataLoader,
    device: torch.device,
    adaptive: bool = False,
) -> Dict[str, float]:
    model.eval()
    correct = 0
    total = 0
    class_correct: Dict[int, int] = {}
    class_total: Dict[int, int] = {}
    for batch in loader:
        waveform = batch["waveform"].to(device)
        frames = batch["frames"].to(device)
        labels = batch["label"].to(device)
        frame_mask = batch["frame_mask"].to(device)
        out = model(waveform, frames, frame_mask=frame_mask, adaptive=adaptive)
        logits = criterion.classifier(out["fused"])
        pred = logits.argmax(dim=-1)
        correct += int((pred == labels).sum().item())
        total += labels.numel()
        for y, p in zip(labels.tolist(), pred.tolist()):
            class_total[y] = class_total.get(y, 0) + 1
            class_correct[y] = class_correct.get(y, 0) + int(y == p)
    wa = 100.0 * correct / max(total, 1)
    ua = 100.0 * np.mean([class_correct.get(k, 0) / max(v, 1) for k, v in class_total.items()] or [0.0])
    return {"accuracy": wa, "wa": wa, "ua": ua, "n": float(total)}


def train_one_epoch(
    model: MRAVT,
    criterion: MRAVTCriterion,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    scheduler,
    device: torch.device,
    grad_clip: float,
) -> Dict[str, float]:
    model.train()
    running = 0.0
    n_batches = 0
    for batch in tqdm(loader, leave=False, desc="train"):
        waveform = batch["waveform"].to(device)
        frames = batch["frames"].to(device)
        labels = batch["label"].to(device)
        frame_mask = batch["frame_mask"].to(device)
        optimizer.zero_grad(set_to_none=True)
        out = model(waveform, frames, frame_mask=frame_mask, adaptive=False)
        # Training-set augmentation for the MMD term (source-derived perturbation).
        wav_aug = waveform + 0.01 * torch.randn_like(waveform)
        out_aug = model(wav_aug, frames, frame_mask=frame_mask, adaptive=False)
        losses = criterion(
            fused=out["fused"],
            labels=labels,
            branch_summaries=out["branch_summaries"],
            gate_logits=out["gate_logits"],
            align_loss=out["align_loss"],
            cm_loss=out["cm_loss"],
            fused_aug=out_aug["fused"].detach(),
        )
        losses["loss"].backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
        optimizer.step()
        scheduler.step()
        running += float(losses["loss"].item())
        n_batches += 1
    return {"loss": running / max(n_batches, 1)}


def build_loaders(cfg: MRAVTConfig, manifest: Optional[str]) -> Dict[str, DataLoader]:
    if not manifest:
        manifest = "data/demo/manifest.csv"
    if not Path(manifest).exists():
        raise FileNotFoundError(
            f"Manifest not found: {manifest}. Bundled demo lives at data/demo/manifest.csv"
        )
    samples = load_manifest(manifest)
    train_samples = filter_split(samples, "train") or samples
    val_samples = filter_split(samples, "val") or filter_split(samples, "valid")
    test_samples = filter_split(samples, "test")
    if not val_samples:
        val_samples = train_samples[: max(1, len(train_samples) // 10)] or train_samples
    kwargs = dict(
        sample_rate=cfg.sample_rate,
        max_audio_seconds=cfg.max_audio_seconds,
        num_visual_frames=cfg.num_visual_frames,
        image_size=cfg.image_size,
    )
    train_ds = ManifestDataset(train_samples, augment=True, **kwargs)
    val_ds = ManifestDataset(val_samples, augment=False, **kwargs)
    loaders = {
        "train": DataLoader(
            train_ds,
            batch_size=cfg.train.batch_size,
            shuffle=True,
            num_workers=cfg.train.num_workers,
            collate_fn=collate_batch,
        ),
        "val": DataLoader(
            val_ds,
            batch_size=cfg.train.batch_size,
            shuffle=False,
            num_workers=cfg.train.num_workers,
            collate_fn=collate_batch,
        ),
    }
    if test_samples:
        loaders["test"] = DataLoader(
            ManifestDataset(test_samples, augment=False, **kwargs),
            batch_size=cfg.train.batch_size,
            shuffle=False,
            num_workers=cfg.train.num_workers,
            collate_fn=collate_batch,
        )
    return loaders


def run_training(cfg: MRAVTConfig, manifest: str, output_dir: str, device: str) -> Dict[str, float]:
    set_seed(cfg.seed)
    device_t = torch.device(device if torch.cuda.is_available() or device == "cpu" else "cpu")
    if device == "cuda" and not torch.cuda.is_available():
        device_t = torch.device("cpu")
    model = MRAVT(cfg).to(device_t)
    criterion = MRAVTCriterion(
        num_classes=cfg.num_classes,
        dim=cfg.model.dim,
        temperature=cfg.model.contrastive_tau,
        lambdas={
            "cls": cfg.train.lambda_cls,
            "con": cfg.train.lambda_con,
            "aug": cfg.train.lambda_aug,
            "cm": cfg.train.lambda_cm,
            "align": cfg.train.lambda_align,
            "gate": cfg.train.lambda_gate,
        },
    ).to(device_t)
    loaders = build_loaders(cfg, manifest)
    optimizer = torch.optim.AdamW(list(model.parameters()) + list(criterion.parameters()), lr=cfg.train.lr, weight_decay=cfg.train.weight_decay)
    steps = cfg.train.epochs * max(1, len(loaders["train"]))
    warmup = int(cfg.train.warmup_ratio * steps)
    scheduler = torch.optim.lr_scheduler.LambdaLR(
        optimizer, lambda step: cosine_warmup_lambda(step, warmup, steps)
    )
    best = -1.0
    patience = 0
    history = []
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    for epoch in range(1, cfg.train.epochs + 1):
        train_stats = train_one_epoch(model, criterion, loaders["train"], optimizer, scheduler, device_t, cfg.train.grad_clip)
        val_stats = evaluate(model, criterion, loaders["val"], device_t, adaptive=False)
        record = {"epoch": epoch, **train_stats, **{f"val_{k}": v for k, v in val_stats.items()}}
        history.append(record)
        metric = val_stats["ua"] if cfg.dataset in {"baum-1s", "iemocap"} else val_stats["accuracy"]
        print(f"epoch {epoch}: loss={train_stats['loss']:.4f} val_acc={val_stats['accuracy']:.2f}")
        if metric > best:
            best = metric
            patience = 0
            torch.save({"model": model.state_dict(), "criterion": criterion.state_dict(), "cfg": cfg.__dict__}, out_path / "best.pt")
        else:
            patience += 1
            if patience >= cfg.train.patience:
                break
    (out_path / "history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    return {"best_val": best}


@torch.no_grad()
def robustness_sweep(model: MRAVT, criterion: MRAVTCriterion, loader: DataLoader, device: torch.device) -> Dict[str, Dict[str, float]]:
    model.eval()
    results = {}

    def _eval(corrupt_fn) -> Dict[str, float]:
        correct = total = 0
        for batch in loader:
            waveform = batch["waveform"].to(device)
            frames = batch["frames"].to(device)
            labels = batch["label"].to(device)
            frame_mask = batch["frame_mask"].to(device)
            waveform, frames, frame_mask, a_mod, v_mod = corrupt_fn(waveform, frames, frame_mask)
            out = model(
                waveform,
                frames,
                frame_mask=frame_mask,
                audio_mask_mod=a_mod,
                visual_mask_mod=v_mod,
            )
            pred = criterion.classifier(out["fused"]).argmax(dim=-1)
            correct += int((pred == labels).sum().item())
            total += labels.numel()
        return {"accuracy": 100.0 * correct / max(total, 1)}

    for snr in (20, 10, 5, 0):
        results[f"gaussian_{snr}db"] = _eval(
            lambda w, f, m, snr=snr: (add_gaussian_noise(w, snr), f, m, None, None)
        )
    for drop in (0.0, 0.25, 0.5, 0.75):
        def _drop(w, f, m, drop=drop):
            frames_d, mask_d = visual_frame_dropout(f, drop, m)
            return w, frames_d, mask_d, None, None

        results[f"visual_drop_{int(drop * 100)}"] = _eval(_drop)
    results["missing_audio"] = _eval(lambda w, f, m: (torch.zeros_like(w), f, m, torch.zeros(w.size(0), device=w.device), None))
    results["missing_visual"] = _eval(lambda w, f, m: (w, torch.zeros_like(f), torch.zeros_like(m), None, torch.zeros(w.size(0), device=w.device)))
    results["imbalance_audio_5db"] = _eval(lambda w, f, m: (add_gaussian_noise(w, 5.0), f, m, None, None))
    def _imbalance_visual(w, f, m):
        frames_d, mask_d = visual_frame_dropout(f, 0.5, m)
        return w, frames_d, mask_d, None, None

    results["imbalance_visual_50"] = _eval(_imbalance_visual)
    for kind in ("babble", "traffic", "pink"):
        results[f"{kind}_5db"] = _eval(lambda w, f, m, kind=kind: (add_colored_noise(w, 5.0, kind), f, m, None, None))
    results["reverb_t60_0.6"] = _eval(lambda w, f, m: (apply_reverb(w, 0.6), f, m, None, None))
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train or evaluate MR-AVT")
    parser.add_argument("--config", default="configs/demo.yaml")
    parser.add_argument("--manifest", default="data/demo/manifest.csv")
    parser.add_argument("--output", default="outputs/demo")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--tiny", action="store_true", help="Use the unit-test architecture")
    parser.add_argument("--eval-only", action="store_true")
    parser.add_argument("--checkpoint", default=None)
    parser.add_argument("--robustness", action="store_true")
    parser.add_argument("--num-classes", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = MRAVTConfig.tiny() if args.tiny else MRAVTConfig.from_yaml(args.config)
    if args.num_classes:
        cfg.num_classes = args.num_classes
    if args.eval_only:
        device_t = torch.device(args.device if torch.cuda.is_available() else "cpu")
        model = MRAVT(cfg).to(device_t)
        criterion = MRAVTCriterion(
            cfg.num_classes,
            cfg.model.dim,
            cfg.model.contrastive_tau,
            {
                "cls": cfg.train.lambda_cls,
                "con": cfg.train.lambda_con,
                "aug": cfg.train.lambda_aug,
                "cm": cfg.train.lambda_cm,
                "align": cfg.train.lambda_align,
                "gate": cfg.train.lambda_gate,
            },
        ).to(device_t)
        if args.checkpoint:
            ckpt = torch.load(args.checkpoint, map_location=device_t)
            model.load_state_dict(ckpt["model"], strict=False)
            if "criterion" in ckpt:
                criterion.load_state_dict(ckpt["criterion"], strict=False)
        loaders = build_loaders(cfg, args.manifest)
        split = "test" if "test" in loaders else "val"
        stats = evaluate(model, criterion, loaders[split], device_t, adaptive=True)
        print(json.dumps(stats, indent=2))
        if args.robustness:
            rob = robustness_sweep(model, criterion, loaders[split], device_t)
            print(json.dumps(rob, indent=2))
        return
    run_training(cfg, args.manifest, args.output, args.device)


if __name__ == "__main__":
    main()
