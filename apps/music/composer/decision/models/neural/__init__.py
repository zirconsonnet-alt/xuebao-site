try:
    from .tcn import TCNConfig, TCNScorer

    __all__ = ["TCNConfig", "TCNScorer"]
except ModuleNotFoundError as e:
    # Optional dependency (torch). Allow importing decision.* without torch installed.
    if e.name != "torch":
        raise

    __all__ = ["TCNConfig", "TCNScorer"]

    class TCNScorer:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs) -> None:
            raise ModuleNotFoundError("torch is required for TCNScorer (pip install torch)")

    class TCNConfig:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs) -> None:
            raise ModuleNotFoundError("torch is required for TCNConfig (pip install torch)")
