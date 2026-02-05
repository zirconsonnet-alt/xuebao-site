# Module for schema
from dataclasses import dataclass, field


@dataclass
class ComposerConfig:
    seed: int = 42
    decision: "DecisionConfig" = field(default_factory=lambda: DecisionConfig())


@dataclass
class DecisionLocalScorerConfig:
    kind: str = "tcn"
    tcn_window: int = 8


@dataclass
class DecisionGlobalRerankerConfig:
    kind: str = "xgboost"
    top_n: int = 100
    feature_pool: str = "mean"


@dataclass
class DecisionBeamConfig:
    width: int = 16
    candidates_per_step: int = 30
    eos_enabled: bool = True


@dataclass
class DecisionConfig:
    local_scorer: DecisionLocalScorerConfig = field(default_factory=DecisionLocalScorerConfig)
    global_reranker: DecisionGlobalRerankerConfig = field(default_factory=DecisionGlobalRerankerConfig)
    beam: DecisionBeamConfig = field(default_factory=DecisionBeamConfig)
