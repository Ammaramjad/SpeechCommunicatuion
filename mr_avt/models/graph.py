"""Heterogeneous audio--visual graph construction and GAT message passing."""

from __future__ import annotations

from typing import Dict, Tuple

import torch
from torch import nn
from torch.nn import functional as F

from ..config import ModelConfig
from .layers import masked_mean


class GraphAttentionLayer(nn.Module):
    def __init__(self, dim: int, heads: int, dropout: float) -> None:
        super().__init__()
        self.heads = heads
        self.head_dim = dim // heads
        assert dim % heads == 0
        self.W = nn.Linear(dim, dim, bias=False)
        self.attn = nn.Parameter(torch.randn(heads, 2 * self.head_dim) * 0.02)
        self.leaky = nn.LeakyReLU(0.2)
        self.out = nn.Linear(dim, dim)
        self.dropout = nn.Dropout(dropout)

    def forward(self, h: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        """
        h: [B, N, D], adj: [B, N, N] binary/sparse neighborhood mask.
        """
        bsz, n, _ = h.shape
        wh = self.W(h).view(bsz, n, self.heads, self.head_dim)
        hi = wh.unsqueeze(2).expand(-1, -1, n, -1, -1)
        hj = wh.unsqueeze(1).expand(-1, n, -1, -1, -1)
        cat = torch.cat([hi, hj], dim=-1)
        e = self.leaky((cat * self.attn).sum(dim=-1))  # [B, N, N, H]
        e = e.masked_fill(adj.unsqueeze(-1) < 0.5, -1e9)
        alpha = torch.softmax(e, dim=2)
        alpha = self.dropout(alpha)
        out = (alpha.unsqueeze(-1) * hj).sum(dim=2)
        out = out.reshape(bsz, n, -1)
        return F.elu(self.out(out))


class HeterogeneousAVGraph(nn.Module):
    def __init__(self, cfg: ModelConfig) -> None:
        super().__init__()
        self.cfg = cfg
        self.audio_proj = nn.Linear(cfg.dim, cfg.dim)
        self.visual_proj = nn.Linear(cfg.dim, cfg.dim)
        self.layers = nn.ModuleList(
            [GraphAttentionLayer(cfg.dim, cfg.graph_heads, cfg.dropout) for _ in range(cfg.graph_layers)]
        )
        self.cm_head_a = nn.Linear(cfg.dim, cfg.dim)
        self.cm_head_v = nn.Linear(cfg.dim, cfg.dim)

    def _subsample(self, tokens: torch.Tensor, mask: torch.Tensor, limit: int) -> Tuple[torch.Tensor, torch.Tensor]:
        length = tokens.size(1)
        if length <= limit:
            return tokens, mask
        idx = torch.linspace(0, length - 1, limit, device=tokens.device).round().long()
        return tokens[:, idx], mask[:, idx]

    def build_nodes(
        self,
        audio_tokens: Dict[str, torch.Tensor],
        audio_masks: Dict[str, torch.Tensor],
        visual_tokens: torch.Tensor,
        visual_mask: torch.Tensor | None,
    ) -> Tuple[torch.Tensor, torch.Tensor, int, Dict[str, slice]]:
        pieces = []
        masks = []
        slices: Dict[str, slice] = {}
        offset = 0
        for name, tok in audio_tokens.items():
            tok, msk = self._subsample(tok, audio_masks[name], self.cfg.graph_token_limit)
            tok = self.audio_proj(tok)
            pieces.append(tok)
            masks.append(msk)
            end = offset + tok.size(1)
            slices[f"a_{name}"] = slice(offset, end)
            offset = end
        vis = self.visual_proj(visual_tokens)
        if visual_mask is None:
            visual_mask = torch.ones(vis.size(0), vis.size(1), device=vis.device, dtype=torch.bool)
        pieces.append(vis)
        masks.append(visual_mask)
        slices["v"] = slice(offset, offset + vis.size(1))
        nodes = torch.cat(pieces, dim=1)
        node_mask = torch.cat(masks, dim=1)
        n_audio = slices["v"].start
        return nodes, node_mask, n_audio, slices

    def build_adjacency(self, nodes: torch.Tensor, node_mask: torch.Tensor, n_audio: int, slices: Dict[str, slice]) -> torch.Tensor:
        bsz, n, _ = nodes.shape
        adj = nodes.new_zeros(bsz, n, n)
        # Temporal edges within each audio resolution and the visual stream.
        for sl in slices.values():
            length = sl.stop - sl.start
            if length <= 1:
                continue
            idx = torch.arange(length - 1, device=nodes.device)
            adj[:, sl.start + idx, sl.start + idx + 1] = 1
            adj[:, sl.start + idx + 1, sl.start + idx] = 1
        # Semantic k-NN edges using Gaussian affinity on common-dimensional features.
        valid = node_mask.unsqueeze(1) & node_mask.unsqueeze(2)
        dist = torch.cdist(nodes, nodes, p=2)
        affinity = torch.exp(-dist.pow(2) / self.cfg.graph_tau)
        affinity = affinity.masked_fill(~valid, 0.0)
        k = min(self.cfg.graph_k, n)
        _, knn = torch.topk(affinity, k=k, dim=-1)
        semantic = torch.zeros_like(adj)
        semantic.scatter_(-1, knn, 1.0)
        adj = torch.clamp(adj + semantic, max=1.0)
        eye = torch.eye(n, device=nodes.device).unsqueeze(0)
        adj = torch.clamp(adj + eye, max=1.0)
        adj = adj.masked_fill(~valid, 0.0)
        return adj

    def forward(
        self,
        audio_tokens: Dict[str, torch.Tensor],
        audio_masks: Dict[str, torch.Tensor],
        visual_tokens: torch.Tensor,
        visual_mask: torch.Tensor | None = None,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        nodes, node_mask, n_audio, slices = self.build_nodes(
            audio_tokens, audio_masks, visual_tokens, visual_mask
        )
        adj = self.build_adjacency(nodes, node_mask, n_audio, slices)
        h = nodes
        for layer in self.layers:
            h = h + layer(h, adj)
        audio_h = h[:, :n_audio]
        visual_h = h[:, n_audio:]
        audio_mask = node_mask[:, :n_audio]
        vis_mask = node_mask[:, n_audio:]
        z_a = masked_mean(audio_h, audio_mask)
        z_v = masked_mean(visual_h, vis_mask)
        # Cross-modal consistency on projected graph-refined embeddings.
        a_n = F.normalize(self.cm_head_a(z_a), dim=-1)
        v_n = F.normalize(self.cm_head_v(z_v), dim=-1)
        cm_loss = (1.0 - (a_n * v_n).sum(dim=-1)).mean()
        return z_a, z_v, cm_loss
