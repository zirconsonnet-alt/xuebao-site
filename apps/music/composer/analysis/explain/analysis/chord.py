# Analysis explanations for chord
from dataclasses import dataclass
from typing import Dict

from ....domain.chord import Chord
from ....domain.enums.core import Degrees
from ..view import AnalysisView, Field, FieldGroup, FieldSource, FieldSpec


@dataclass(frozen=True, slots=True)
class ChordAnalysis:
    chord: Chord
    tension_score: float
    target_note_tendencies: Dict[Degrees, float]

    def view(self) -> AnalysisView:
        def _spec(
            key: str,
            group: FieldGroup,
            title: str,
            typ: object,
            *,
            source: FieldSource,
            stable: bool = True,
            jsonable: bool = False,
        ) -> FieldSpec:
            return FieldSpec(
                key=key,
                group=group,
                title=title,
                typ=typ,
                source=source,
                stable=stable,
                jsonable=jsonable,
            )

        fields = [
            Field(
                spec=_spec(
                    key="kind",
                    group=FieldGroup.META,
                    title="analysis kind",
                    typ=str,
                    source=FieldSource.ANALYSIS,
                ),
                getter=lambda _: "Chord",
            ),
            Field(
                spec=_spec(
                    key="chord",
                    group=FieldGroup.ENTITY,
                    title="chord",
                    typ=object,
                    source=FieldSource.ANALYSIS,
                ),
                getter=lambda a: a.chord,
            ),
            Field(
                spec=_spec(
                    key="tension_score",
                    group=FieldGroup.ANALYSIS,
                    title="tension score (0..10)",
                    typ=float,
                    source=FieldSource.ANALYSIS,
                    jsonable=True,
                ),
                getter=lambda a: a.tension_score,
            ),
            Field(
                spec=_spec(
                    key="target_note_tendencies",
                    group=FieldGroup.ANALYSIS,
                    title="next target degree tendencies (root=I)",
                    typ=dict,
                    source=FieldSource.ANALYSIS,
                    jsonable=True,
                ),
                getter=lambda a: {k.name: v for k, v in a.target_note_tendencies.items()},
            ),
        ]
        return AnalysisView(self, fields)
