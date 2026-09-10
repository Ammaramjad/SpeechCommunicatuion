"""MR-AVT: multi-resolution audio--visual transformer with graph fusion."""

from __future__ import annotations

from typing import Dict, Optional

import torch
from torch import nn

from ..config import MRAVTConfig
from .audio import MultiResolutionAudioEncoder, compute_log_mel
from .fusion import BranchGate, UncertaintyAwareFusion
from .graph import HeterogeneousAVGraph
from .visual import VisualEncoder


class MRAVT(nn.Module):
    def __init__(self, config: MRAVTConfig) -> None:
        super().__init__()
        self.config = config
        self.audio = MultiResolutionAudioEncoder(config)
        self.visual = VisualEncoder(config)
        self.graph = HeterogeneousAVGraph(config.model)
        self.fusion = UncertaintyAwareFusion(config.model.dim)
        self.gate = BranchGate(config.n_mels, config.model.dim)
        self.branch_names = list(config.resolutions.keys())

    def spectrograms(self, waveform: torch.Tensor) -> tuple[Dict[str, torch.Tensor], Dict[str, torch.Tensor]]:
        specs, masks = {}, {}
        for name, spec in self.config.resolutions.items():
            specs[name], masks[name] = compute_log_mel(
                waveform,
                spec,
                n_mels=self.config.n_mels,
                sample_rate=self.config.sample_rate,
                max_frames=self.config.temporal_frames,
            )
        return specs, masks

    def forward(
        self,
        waveform: torch.Tensor,
        frames: torch.Tensor,
        *,
        audio_mask_mod: Optional[torch.Tensor] = None,
        visual_mask_mod: Optional[torch.Tensor] = None,
        frame_mask: Optional[torch.Tensor] = None,
        adaptive: bool = False,
        return_aux: bool = True,
    ) -> Dict[str, torch.Tensor]:
        specs, spec_masks = self.spectrograms(waveform)
        _, gate_logits = self.gate(specs["s"])

        if adaptive and not self.training:
            active = self.gate.select_branches(gate_logits, self.config.model.gate_delta)
        else:
            active = torch.ones(waveform.size(0), len(self.branch_names), device=waveform.device, dtype=torch.bool)

        tokens = self.audio.encode_all(specs, spec_masks, active=None if self.training or not adaptive else {
            name: active[:, i] for i, name in enumerate(self.branch_names)
        })
        if adaptive and not self.training:
            for i, name in enumerate(self.branch_names):
                drop = ~active[:, i]
                if drop.any():
                    tokens[name] = tokens[name].masked_fill(drop[:, None, None], 0.0)
                    spec_masks[name] = spec_masks[name] & (~drop)[:, None]

        z_audio_branch, align_loss, branch_summaries = self.audio.cross_resolution(
            tokens, spec_masks, active_mask=active.float()
        )
        z_visual, visual_tokens = self.visual(frames, frame_mask)

        if audio_mask_mod is not None:
            z_audio_branch = z_audio_branch * audio_mask_mod.unsqueeze(-1)
            visual_tokens = visual_tokens  # unchanged
            for name in tokens:
                tokens[name] = tokens[name] * audio_mask_mod[:, None, None]
        if visual_mask_mod is not None:
            z_visual = z_visual * visual_mask_mod.unsqueeze(-1)
            visual_tokens = visual_tokens * visual_mask_mod[:, None, None]

        graph_a, graph_v, cm_loss = self.graph(tokens, spec_masks, visual_tokens, frame_mask)
        if audio_mask_mod is not None:
            graph_a = graph_a * audio_mask_mod.unsqueeze(-1)
        if visual_mask_mod is not None:
            graph_v = graph_v * visual_mask_mod.unsqueeze(-1)

        fused, weights, uncertainties = self.fusion(graph_a, graph_v)
        out = {
            "fused": fused,
            "gate_logits": gate_logits,
            "align_loss": align_loss,
            "cm_loss": cm_loss,
            "branch_summaries": branch_summaries,
            "fusion_weights": weights,
            "uncertainties": uncertainties,
            "active_branches": active,
            "z_audio": graph_a,
            "z_visual": graph_v,
            "spectrograms": specs,
        }
        if not return_aux:
            return {"fused": fused, "gate_logits": gate_logits}
        return out
