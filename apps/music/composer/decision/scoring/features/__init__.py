try:
    from .sequence_features import (
        SequenceFeaturesConfig,
        build_step_vector,
        build_sequence_vectors,
        pad_window,
        extract_sequence_features,
        to_feature_vector,
    )

    __all__ = [
        "SequenceFeaturesConfig",
        "build_step_vector",
        "build_sequence_vectors",
        "pad_window",
        "extract_sequence_features",
        "to_feature_vector",
    ]
except ModuleNotFoundError as e:
    # Optional dependency (torch) via TCN features.
    if e.name != "torch":
        raise

    __all__ = []
