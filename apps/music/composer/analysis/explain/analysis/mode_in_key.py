# Analysis explanations for mode in key
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet

from ...core.hits.mode_in_key import ModeInKeyHit
from ....domain.chord import Chord
from ....domain.enums.core import Degrees
from ....domain.enums.harmony import Functions
from ..view import AnalysisView, Field, FieldGroup, FieldSource, FieldSpec


@dataclass(frozen=True, slots=True)
class ModeInKeyAnalysis:
    hit: ModeInKeyHit
    tonic_interval: int
    altered_degrees: FrozenSet[Degrees]

    skeleton_chord: Chord
    skeleton_function_scores: Dict[Functions, float]
    skeleton_function_tendencies: Dict[Functions, float]

    def view(self) -> AnalysisView:
        hit = self.hit

        def _spec(
            key: str,
            group: FieldGroup,
            title: str,
            typ: object,
            *,
            source: FieldSource,
            jsonable: bool = False,
        ) -> FieldSpec:
            return FieldSpec(key=key, group=group, title=title, typ=typ, source=source, jsonable=jsonable)

        fields = [
            Field(_spec("kind", FieldGroup.META, "resolve kind", str, source=FieldSource.ANALYSIS), lambda _: hit.kind.name),
            Field(_spec("key", FieldGroup.ENTITY, "key", object, source=FieldSource.HIT), lambda _: hit.key),
            Field(_spec("mode", FieldGroup.ENTITY, "mode", object, source=FieldSource.HIT), lambda _: hit.mode),
            Field(_spec("access", FieldGroup.ENTITY, "access", object, source=FieldSource.HIT), lambda _: hit.access),
            Field(_spec("role", FieldGroup.ENTITY, "role", object, source=FieldSource.HIT), lambda _: hit.role),
            Field(_spec("tonic_interval", FieldGroup.EVIDENCE, "tonic interval", int, source=FieldSource.HIT), lambda _: hit.tonic_interval()),
            Field(
                _spec(
                    "altered_degrees",
                    FieldGroup.EVIDENCE,
                    "altered degrees",
                    FrozenSet[Degrees],
                    source=FieldSource.HIT,
                    jsonable=True,
                ),
                lambda _: hit.altered_degrees(),
                serializer=lambda s: [d.name for d in sorted(s, key=lambda d: d.value)],
            ),
            Field(
                _spec(
                    "skeleton_chord",
                    FieldGroup.EVIDENCE,
                    "skeleton chord (mode I triad, Base)",
                    object,
                    source=FieldSource.HIT,
                ),
                lambda _: hit.skeleton_chord(),
            ),
            Field(
                _spec(
                    "skeleton_function_scores",
                    FieldGroup.ANALYSIS,
                    "skeleton function scores",
                    dict,
                    source=FieldSource.ANALYSIS,
                    jsonable=True,
                ),
                lambda _: {k.name: v for k, v in self.skeleton_function_scores.items()},
            ),
            Field(
                _spec(
                    "skeleton_function_tendencies",
                    FieldGroup.ANALYSIS,
                    "skeleton function tendencies",
                    dict,
                    source=FieldSource.ANALYSIS,
                    jsonable=True,
                ),
                lambda _: {k.name: v for k, v in self.skeleton_function_tendencies.items()},
            ),
        ]
        return AnalysisView(self, fields)

    def __str__(self) -> str:
        altered = ", ".join(d.name for d in sorted(self.altered_degrees, key=lambda d: d.value)) or "None"
        return (
            f"ModeInKeyAnalysis(mode={self.hit.mode}, key={self.hit.key}, "
            f"interval={self.tonic_interval}, altered=[{altered}], skeleton={self.skeleton_chord})"
        )

