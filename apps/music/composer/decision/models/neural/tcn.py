from dataclasses import dataclass
from typing import List, Sequence, Tuple

try:
    import torch  # type: ignore
    import torch.nn as nn  # type: ignore
    import torch.nn.functional as F  # type: ignore
except ModuleNotFoundError as e:
    if e.name != "torch":
        raise
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]
    F = None  # type: ignore[assignment]


@dataclass(frozen=True, slots=True)
class TCNConfig:
    input_dim: int
    channels: Tuple[int, ...] = (128, 128, 128)
    kernel_size: int = 3
    dropout: float = 0.1
    use_layernorm: bool = True


if torch is not None:

    class _Chomp1d(nn.Module):
        def __init__(self, chomp_size: int):
            super().__init__()
            self.chomp_size = int(chomp_size)

        def forward(self, x: "torch.Tensor") -> "torch.Tensor":
            if self.chomp_size <= 0:
                return x
            return x[:, :, :-self.chomp_size]

    class _TemporalBlock(nn.Module):
        def __init__(
            self,
            in_ch: int,
            out_ch: int,
            *,
            kernel_size: int,
            dilation: int,
            dropout: float,
            use_layernorm: bool,
        ):
            super().__init__()
            if kernel_size < 2:
                raise ValueError("kernel_size should be >= 2")

            pad = (kernel_size - 1) * dilation

            self.conv1 = nn.Conv1d(in_ch, out_ch, kernel_size, padding=pad, dilation=dilation)
            self.chomp1 = _Chomp1d(pad)
            self.conv2 = nn.Conv1d(out_ch, out_ch, kernel_size, padding=pad, dilation=dilation)
            self.chomp2 = _Chomp1d(pad)

            self.dropout = nn.Dropout(dropout)

            self.use_layernorm = bool(use_layernorm)
            if self.use_layernorm:
                self.ln1 = nn.LayerNorm(out_ch)
                self.ln2 = nn.LayerNorm(out_ch)

            self.downsample = nn.Conv1d(in_ch, out_ch, kernel_size=1) if in_ch != out_ch else None

        @staticmethod
        def _maybe_ln(x_bct: "torch.Tensor", ln: "nn.LayerNorm") -> "torch.Tensor":
            x_btc = x_bct.transpose(1, 2)
            x_btc = ln(x_btc)
            return x_btc.transpose(1, 2)

        def forward(self, x: "torch.Tensor") -> "torch.Tensor":
            y = self.conv1(x)
            y = self.chomp1(y)
            if self.use_layernorm:
                y = self._maybe_ln(y, self.ln1)
            y = F.relu(y)
            y = self.dropout(y)

            y = self.conv2(y)
            y = self.chomp2(y)
            if self.use_layernorm:
                y = self._maybe_ln(y, self.ln2)
            y = F.relu(y)
            y = self.dropout(y)

            res = x if self.downsample is None else self.downsample(x)
            return F.relu(y + res)

    class TCNScorer(nn.Module):
        def __init__(self, cfg: TCNConfig):
            super().__init__()
            self.cfg = cfg

            layers: List["nn.Module"] = []
            in_ch = cfg.input_dim
            for i, out_ch in enumerate(cfg.channels):
                dilation = 2**i
                layers.append(
                    _TemporalBlock(
                        in_ch,
                        out_ch,
                        kernel_size=cfg.kernel_size,
                        dilation=dilation,
                        dropout=cfg.dropout,
                        use_layernorm=cfg.use_layernorm,
                    )
                )
                in_ch = out_ch
            self.tcn = nn.Sequential(*layers)

            self.head = nn.Conv1d(in_ch, 1, kernel_size=1)

        @property
        def receptive_field(self) -> int:
            k = self.cfg.kernel_size
            s = sum(2**i for i in range(len(self.cfg.channels)))
            return 1 + (k - 1) * s

        def forward(self, x_btd: "torch.Tensor", *, return_sequence: bool = True) -> "torch.Tensor":
            if x_btd.dim() != 3:
                raise ValueError("x must be (B, T, D)")
            _, _, d = x_btd.shape
            if d != self.cfg.input_dim:
                raise ValueError(f"input_dim mismatch: got {d}, expected {self.cfg.input_dim}")

            x = x_btd.transpose(1, 2)
            y = self.tcn(x)
            s = self.head(y).squeeze(1)

            if return_sequence:
                return s
            return s[:, -1:].contiguous()

        def encode(self, x_btd: "torch.Tensor") -> "torch.Tensor":
            if x_btd.dim() != 3:
                raise ValueError("x must be (B, T, D)")
            _, _, d = x_btd.shape
            if d != self.cfg.input_dim:
                raise ValueError(f"input_dim mismatch: got {d}, expected {self.cfg.input_dim}")
            x = x_btd.transpose(1, 2)
            y = self.tcn(x)
            return y.transpose(1, 2)

        def embed(
            self,
            x_btd: "torch.Tensor",
            *,
            pool: str = "mean",
            lengths: "torch.Tensor | None" = None,
        ) -> "torch.Tensor":
            h_btc = self.encode(x_btd)
            if pool == "last":
                if lengths is None:
                    return h_btc[:, -1, :]
                idx = (lengths - 1).clamp_min(0).long()
                batch = torch.arange(h_btc.size(0), device=h_btc.device)
                return h_btc[batch, idx, :]
            if pool != "mean":
                raise ValueError("pool must be 'mean' or 'last'")
            if lengths is None:
                return h_btc.mean(dim=1)
            max_len = h_btc.size(1)
            mask = torch.arange(max_len, device=h_btc.device).unsqueeze(0) < lengths.unsqueeze(1)
            mask = mask.unsqueeze(-1).to(h_btc.dtype)
            summed = (h_btc * mask).sum(dim=1)
            denom = mask.sum(dim=1).clamp_min(1.0)
            return summed / denom

        @torch.no_grad()
        def score_window(self, x_btd: "torch.Tensor") -> "torch.Tensor":
            s_last = self.forward(x_btd, return_sequence=False)
            return s_last.squeeze(-1)

        @torch.no_grad()
        def score_candidates(self, windows: Sequence["torch.Tensor"]) -> "torch.Tensor":
            if not windows:
                return torch.empty((0,), dtype=torch.float32)
            x = torch.stack(list(windows), dim=0)
            return self.score_window(x)
else:

    class TCNScorer:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs) -> None:
            raise ModuleNotFoundError("torch is required for TCNScorer (pip install torch)")
