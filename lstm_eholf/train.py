"""Training loop: Adam + cosine annealing + class-weighted CE + balanced sampler."""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler

from lstm_eholf.config import LSTMConfig
from lstm_eholf.metrics import class_weights, precision_recall_f1, roc_auc_ovr, unweighted_accuracy, weighted_accuracy
from lstm_eholf.models import build_classifier, count_parameters


class SeqDataset(Dataset):
    def __init__(self, x: np.ndarray, y: np.ndarray, lengths: np.ndarray):
        self.x = torch.from_numpy(x.astype(np.float32))
        self.y = torch.from_numpy(y.astype(np.int64))
        self.lengths = torch.from_numpy(lengths.astype(np.int64))

    def __len__(self):
        return self.x.shape[0]

    def __getitem__(self, i):
        return self.x[i], self.y[i], self.lengths[i]


def _balanced_sampler(y: np.ndarray) -> WeightedRandomSampler:
    counts = np.bincount(y)
    counts = np.maximum(counts, 1)
    w = 1.0 / counts[y]
    return WeightedRandomSampler(torch.from_numpy(w.astype(np.float64)), num_samples=len(y), replacement=True)


def train_model(
    cfg: LSTMConfig,
    train: Tuple[np.ndarray, np.ndarray, np.ndarray],
    val: Tuple[np.ndarray, np.ndarray, np.ndarray],
    architecture: str = "lstm",
    device: Optional[str] = None,
) -> Tuple[nn.Module, Dict[str, float]]:
    device = device or cfg.device
    x_tr, y_tr, l_tr = train
    x_va, y_va, l_va = val
    model = build_classifier(architecture, x_tr.shape[-1], int(cfg.hidden), cfg.layers, cfg.dropout, cfg.num_classes)
    model.to(device)
    w = class_weights(y_tr, cfg.num_classes)
    criterion = nn.CrossEntropyLoss(weight=torch.tensor(w, dtype=torch.float32, device=device))
    opt = torch.optim.Adam(model.parameters(), lr=cfg.lr, weight_decay=cfg.l2)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max(cfg.max_epochs, 1))
    loader = DataLoader(
        SeqDataset(x_tr, y_tr, l_tr),
        batch_size=cfg.batch_size,
        sampler=_balanced_sampler(y_tr),
    )
    best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
    best_val = -1.0
    patience = 0
    train_acc = 0.0
    for epoch in range(cfg.max_epochs):
        model.train()
        for xb, yb, lb in loader:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            logits = model(xb, lb)
            loss = criterion(logits, yb)
            if architecture == "gan" and hasattr(model, "adversarial_step"):
                d_real, d_fake = model.adversarial_step(xb)
                loss = loss + 0.1 * (torch.mean(torch.relu(1 - d_real)) + torch.mean(torch.relu(1 + d_fake)))
            loss.backward()
            opt.step()
        sched.step()
        va = evaluate(model, val, cfg.num_classes, device)
        tr = evaluate(model, train, cfg.num_classes, device)
        train_acc = tr["wa"]
        if va["wa"] > best_val:
            best_val = va["wa"]
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            patience = 0
        else:
            patience += 1
            if patience >= cfg.patience:
                break
    model.load_state_dict(best_state)
    stats = {"train_wa": train_acc, "val_wa": best_val, "params": float(count_parameters(model))}
    return model, stats


@torch.no_grad()
def predict(model: nn.Module, split: Tuple[np.ndarray, np.ndarray, np.ndarray], device: str) -> Tuple[np.ndarray, np.ndarray]:
    model.eval()
    x, y, l = split
    ds = SeqDataset(x, y, l)
    loader = DataLoader(ds, batch_size=64)
    logits_all = []
    for xb, _, lb in loader:
        xb = xb.to(device)
        logits_all.append(model(xb, lb).cpu().numpy())
    logits = np.concatenate(logits_all, axis=0)
    proba = _softmax(logits)
    pred = proba.argmax(axis=1)
    return pred, proba


def _softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


@torch.no_grad()
def evaluate(model: nn.Module, split: Tuple[np.ndarray, np.ndarray, np.ndarray], n_classes: int, device: str) -> Dict[str, float]:
    pred, proba = predict(model, split, device)
    y = split[1]
    prf = precision_recall_f1(y, pred, n_classes)
    micro, aucs = roc_auc_ovr(y, proba)
    return {
        "wa": weighted_accuracy(y, pred),
        "ua": unweighted_accuracy(y, pred, n_classes),
        "macro_f1": prf["macro_f1"],
        "precision": prf["precision"],
        "auc_micro": micro,
        "aucs": aucs,
        "pred": pred,
        "proba": proba,
        "y": y,
    }


def eholf_fitness_from_data(cfg: LSTMConfig, train, val, architecture: str = "lstm"):
    def fn(theta: np.ndarray) -> float:
        local = LSTMConfig(**{**cfg.to_dict(), "lr": float(theta[0]), "l2": float(theta[1]), "dropout": float(theta[2]), "hidden": int(round(theta[3])), "max_epochs": min(cfg.max_epochs, 5)})
        model, stats = train_model(local, train, val, architecture=architecture, device=cfg.device)
        return 1.0 - stats["val_wa"] / 100.0

    return fn
