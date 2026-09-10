"""Configuration dataclasses for MR-AVT."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass
class ResolutionSpec:
    win_length: int
    hop_length: int
    n_fft: int


@dataclass
class ModelConfig:
    dim: int = 768
    depth: int = 6
    heads: int = 8
    ffn_dim: int = 3072
    dropout: float = 0.1
    graph_layers: int = 2
    graph_heads: int = 8
    graph_k: int = 8
    graph_tau: float = 0.5
    eta: float = 0.1
    gate_delta: float = 0.5
    contrastive_tau: float = 0.07
    graph_token_limit: int = 32
    use_pretrained_vit: bool = False
    patch_size: int = 16
    image_size: int = 224
    n_mels: int = 64
    num_visual_frames: int = 16
    temporal_frames: int = 80


@dataclass
class TrainConfig:
    epochs: int = 100
    batch_size: int = 32
    lr: float = 1e-4
    weight_decay: float = 0.01
    warmup_ratio: float = 0.1
    patience: int = 10
    lambda_cls: float = 1.0
    lambda_con: float = 0.5
    lambda_aug: float = 0.5
    lambda_cm: float = 0.1
    lambda_align: float = 0.1
    lambda_gate: float = 0.05
    num_workers: int = 4
    grad_clip: float = 1.0


@dataclass
class MRAVTConfig:
    seed: int = 42
    dataset: str = "iemocap"
    data_root: str = "data"
    num_classes: int = 4
    sample_rate: int = 16000
    n_mels: int = 64
    max_audio_seconds: float = 8.0
    num_visual_frames: int = 16
    image_size: int = 224
    temporal_frames: int = 80
    resolutions: Dict[str, ResolutionSpec] = field(default_factory=dict)
    model: ModelConfig = field(default_factory=ModelConfig)
    train: TrainConfig = field(default_factory=TrainConfig)
    eval_metric: str = "wa"

    def __post_init__(self) -> None:
        if not self.resolutions:
            self.resolutions = {
                "s": ResolutionSpec(400, 160, 512),
                "m": ResolutionSpec(1600, 400, 2048),
                "l": ResolutionSpec(8000, 1600, 8192),
            }
        self.model.n_mels = self.n_mels
        self.model.num_visual_frames = self.num_visual_frames
        self.model.image_size = self.image_size
        self.model.temporal_frames = self.temporal_frames

    @classmethod
    def from_yaml(cls, path: str | Path) -> "MRAVTConfig":
        with open(path, "r", encoding="utf-8") as handle:
            raw: Dict[str, Any] = yaml.safe_load(handle) or {}
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "MRAVTConfig":
        resolutions = {}
        for key, spec in (raw.get("resolutions") or {}).items():
            resolutions[key] = ResolutionSpec(**spec)
        model = ModelConfig(**(raw.get("model") or {}))
        train = TrainConfig(**(raw.get("train") or {}))
        eval_cfg = raw.get("eval") or {}
        cfg = cls(
            seed=raw.get("seed", 42),
            dataset=raw.get("dataset", "iemocap"),
            data_root=raw.get("data_root", "data"),
            num_classes=raw.get("num_classes", 4),
            sample_rate=raw.get("sample_rate", 16000),
            n_mels=raw.get("n_mels", 64),
            max_audio_seconds=raw.get("max_audio_seconds", 8.0),
            num_visual_frames=raw.get("num_visual_frames", 16),
            image_size=raw.get("image_size", 224),
            temporal_frames=raw.get("temporal_frames", 80),
            resolutions=resolutions,
            model=model,
            train=train,
            eval_metric=eval_cfg.get("metric", raw.get("eval_metric", "wa")),
        )
        return cfg

    @classmethod
    def tiny(cls, num_classes: int = 4) -> "MRAVTConfig":
        """Compact architecture for unit tests and CPU sanity checks."""
        cfg = cls(num_classes=num_classes)
        cfg.model.dim = 64
        cfg.model.depth = 2
        cfg.model.heads = 4
        cfg.model.ffn_dim = 128
        cfg.model.graph_layers = 1
        cfg.model.graph_heads = 2
        cfg.model.graph_token_limit = 8
        cfg.model.patch_size = 16
        cfg.model.image_size = 32
        cfg.image_size = 32
        cfg.n_mels = 8
        cfg.model.n_mels = 8
        cfg.num_visual_frames = 4
        cfg.model.num_visual_frames = 4
        cfg.temporal_frames = 16
        cfg.model.temporal_frames = 16
        cfg.resolutions = {
            "s": ResolutionSpec(32, 16, 64),
            "m": ResolutionSpec(64, 32, 128),
            "l": ResolutionSpec(128, 64, 256),
        }
        return cfg
