"""Hyperparameters matching Table 6 (tab:eholf_hparams) of the manuscript."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple


IEMOCAP_EMOTIONS: Tuple[str, ...] = ("neutral", "sad", "happy", "angry")
SAVEE_EMOTIONS: Tuple[str, ...] = (
    "neutral",
    "sad",
    "angry",
    "happy",
    "surprise",
    "fear",
    "disgust",
)
SHARED4: Tuple[str, ...] = ("angry", "happy", "sad", "neutral")

AUDIO_DIM = 78  # 13 MFCC + delta + delta-delta, mean and std
GEO_DIM = 8
RESNET_DIM = 2048
TEXT_BERT_DIM = 768
TEXT_PCA_K = 12
VIDEO_DIM = RESNET_DIM + GEO_DIM
IEMOCAP_FUSED_DIM = AUDIO_DIM + VIDEO_DIM + TEXT_PCA_K
SAVEE_FUSED_DIM = AUDIO_DIM + VIDEO_DIM


@dataclass
class SearchSpace:
    lr: Tuple[float, float] = (1e-4, 1e-2)
    l2: Tuple[float, float] = (1e-5, 1e-2)
    dropout: Tuple[float, float] = (0.1, 0.5)
    hidden: Tuple[int, int] = (64, 256)

    def lower(self) -> List[float]:
        return [self.lr[0], self.l2[0], self.dropout[0], float(self.hidden[0])]

    def upper(self) -> List[float]:
        return [self.lr[1], self.l2[1], self.dropout[1], float(self.hidden[1])]

    def decode(self, theta) -> Dict[str, float]:
        hidden = int(round(theta[3]))
        hidden = max(self.hidden[0], min(self.hidden[1], hidden))
        return {
            "lr": float(theta[0]),
            "l2": float(theta[1]),
            "dropout": float(theta[2]),
            "hidden": float(hidden),
        }


@dataclass
class LSTMConfig:
    dataset: str = "iemocap"
    num_classes: int = 4
    fused_dim: int = IEMOCAP_FUSED_DIM
    layers: int = 2
    hidden: int = 128
    dropout: float = 0.32
    lr: float = 2.3e-3
    l2: float = 4.7e-4
    batch_size: int = 32
    max_epochs: int = 100
    patience: int = 10
    pca_k: int = TEXT_PCA_K
    seed: int = 0
    eholf_population: int = 30
    eholf_tmax: int = 100
    levy_beta: float = 1.5
    aw_min: float = 0.3
    aw_max: float = 0.9
    aw_gamma: float = 2.0
    fusion: str = "concat"
    shap_coalitions: int = 2048
    shap_background: int = 100
    shap_instances: int = 200
    device: str = "cpu"
    max_seq_len: int = 32

    @classmethod
    def iemocap(cls, **kwargs) -> "LSTMConfig":
        defaults = dict(
            dataset="iemocap",
            num_classes=4,
            fused_dim=IEMOCAP_FUSED_DIM,
            dropout=0.32,
            lr=2.3e-3,
            l2=4.7e-4,
            batch_size=32,
            hidden=128,
        )
        defaults.update(kwargs)
        return cls(**defaults)

    @classmethod
    def savee(cls, **kwargs) -> "LSTMConfig":
        defaults = dict(
            dataset="savee",
            num_classes=7,
            fused_dim=SAVEE_FUSED_DIM,
            dropout=0.38,
            lr=3.1e-3,
            l2=8.2e-4,
            batch_size=16,
            hidden=128,
            pca_k=0,
        )
        defaults.update(kwargs)
        return cls(**defaults)

    @classmethod
    def demo(cls, **kwargs) -> "LSTMConfig":
        """Tiny configuration for CI / synthetic reproduction."""
        defaults = dict(
            dataset="demo",
            num_classes=4,
            fused_dim=AUDIO_DIM + GEO_DIM + TEXT_PCA_K,
            layers=1,
            hidden=32,
            dropout=0.2,
            lr=1e-3,
            l2=1e-4,
            batch_size=8,
            max_epochs=3,
            patience=2,
            eholf_population=4,
            eholf_tmax=3,
            shap_coalitions=32,
            shap_background=8,
            shap_instances=16,
            max_seq_len=8,
        )
        defaults.update(kwargs)
        return cls(**defaults)

    def to_dict(self) -> Dict:
        return asdict(self)
