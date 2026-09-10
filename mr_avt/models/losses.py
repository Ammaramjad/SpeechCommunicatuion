"""Training objectives: classification, contrastive, MMD, alignment, gate."""

from __future__ import annotations

from typing import Dict, Optional

import torch
from torch import nn
from torch.nn import functional as F


class SupervisedContrastiveLoss(nn.Module):
    def __init__(self, temperature: float = 0.07) -> None:
        super().__init__()
        self.temperature = temperature

    def forward(self, features: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        feats = F.normalize(features, dim=-1)
        sim = torch.matmul(feats, feats.T) / self.temperature
        logits = sim - torch.max(sim, dim=1, keepdim=True).values.detach()
        labels = labels.view(-1, 1)
        mask = torch.eq(labels, labels.T).to(features.dtype)
        logits_mask = 1.0 - torch.eye(features.size(0), device=features.device)
        mask = mask * logits_mask
        exp_logits = torch.exp(logits) * logits_mask
        log_prob = logits - torch.log(exp_logits.sum(dim=1, keepdim=True).clamp_min(1e-8))
        pos = mask.sum(dim=1)
        loss = -(mask * log_prob).sum(dim=1) / pos.clamp_min(1.0)
        loss = torch.where(pos > 0, loss, torch.zeros_like(loss))
        return loss.mean()


def mmd_rbf(x: torch.Tensor, y: torch.Tensor, sigma: float = 1.0) -> torch.Tensor:
    """Linear-time style MMD in RKHS using a Gaussian kernel on pooled features."""
    xx = torch.matmul(x, x.T)
    yy = torch.matmul(y, y.T)
    xy = torch.matmul(x, y.T)
    rx = xx.diag().unsqueeze(0).expand_as(xx)
    ry = yy.diag().unsqueeze(0).expand_as(yy)
    k_xx = torch.exp(-(rx.T + rx - 2 * xx) / (2 * sigma ** 2))
    k_yy = torch.exp(-(ry.T + ry - 2 * yy) / (2 * sigma ** 2))
    dxx = xx.diag().unsqueeze(1)
    dyy = yy.diag().unsqueeze(0)
    k_xy = torch.exp(-(dxx + dyy - 2 * xy) / (2 * sigma ** 2))
    return k_xx.mean() + k_yy.mean() - 2 * k_xy.mean()


class MRAVTCriterion(nn.Module):
    def __init__(
        self,
        num_classes: int,
        dim: int,
        temperature: float,
        lambdas: Dict[str, float],
    ) -> None:
        super().__init__()
        self.cls = nn.CrossEntropyLoss()
        self.contrastive = SupervisedContrastiveLoss(temperature)
        self.lambdas = lambdas
        self.branch_heads = nn.ModuleDict(
            {name: nn.Linear(dim, num_classes) for name in ("s", "m", "l")}
        )
        self.classifier = nn.Linear(dim, num_classes)

    def forward(
        self,
        fused: torch.Tensor,
        labels: torch.Tensor,
        branch_summaries: Dict[str, torch.Tensor],
        gate_logits: torch.Tensor,
        align_loss: torch.Tensor,
        cm_loss: torch.Tensor,
        fused_aug: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        logits = self.classifier(fused)
        loss_cls = self.cls(logits, labels)
        loss_con = self.contrastive(fused, labels)

        branch_losses = []
        branch_logits = {}
        for name, summary in branch_summaries.items():
            b_logits = self.branch_heads[name](summary)
            branch_logits[name] = b_logits
            branch_losses.append(F.cross_entropy(b_logits, labels, reduction="none"))
        stacked = torch.stack(branch_losses, dim=1)  # [B, 3]
        targets = stacked.argmin(dim=1)
        loss_gate = F.cross_entropy(gate_logits, targets)

        if fused_aug is not None:
            loss_aug = mmd_rbf(F.normalize(fused, dim=-1), F.normalize(fused_aug, dim=-1))
        else:
            loss_aug = fused.new_zeros(())

        align = align_loss.mean() if align_loss.dim() > 0 else align_loss
        total = (
            self.lambdas["cls"] * loss_cls
            + self.lambdas["con"] * loss_con
            + self.lambdas["aug"] * loss_aug
            + self.lambdas["cm"] * cm_loss
            + self.lambdas["align"] * align
            + self.lambdas["gate"] * loss_gate
        )
        return {
            "loss": total,
            "loss_cls": loss_cls.detach(),
            "loss_con": loss_con.detach(),
            "loss_aug": loss_aug.detach() if torch.is_tensor(loss_aug) else fused.new_tensor(0.0),
            "loss_cm": cm_loss.detach(),
            "loss_align": align.detach(),
            "loss_gate": loss_gate.detach(),
            "logits": logits,
            "gate_targets": targets,
        }
