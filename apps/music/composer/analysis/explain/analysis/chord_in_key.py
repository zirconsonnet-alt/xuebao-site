from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from ...core.hits.chord_in_key import ChordInKeyHit
from ....domain.enums.harmony import Functions
from ..view import AnalysisView, Field, FieldGroup, FieldSource, FieldSpec


@dataclass(frozen=True, slots=True)
class ChordInKeyAnalysis:
    hit: ChordInKeyHit

    function_scores: Dict[Functions, float]
    function_tendencies: Dict[Functions, float]
    chromatic_score: float

    def view(self) -> AnalysisView:
        hit = self.hit

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
                    title="resolve kind",
                    typ=str,
                    source=FieldSource.ANALYSIS,
                ),
                getter=lambda _: hit.kind.name,
            ),
            Field(
                spec=_spec(
                    key="key",
                    group=FieldGroup.ENTITY,
                    title="key",
                    typ=object,
                    source=FieldSource.HIT,
                ),
                getter=lambda _: hit.key,
            ),
            Field(
                spec=_spec(
                    key="mode",
                    group=FieldGroup.ENTITY,
                    title="mode",
                    typ=object,
                    source=FieldSource.HIT,
                ),
                getter=lambda _: hit.mode,
            ),
            Field(
                spec=_spec(
                    key="chord",
                    group=FieldGroup.ENTITY,
                    title="chord",
                    typ=object,
                    source=FieldSource.HIT,
                ),
                getter=lambda _: hit.chord,
            ),
            Field(
                spec=_spec(
                    key="altered_degrees",
                    group=FieldGroup.EVIDENCE,
                    title="altered degrees (mode vs key main-mode base)",
                    typ=frozenset,
                    source=FieldSource.HIT,
                    jsonable=True,
                ),
                getter=lambda _: hit.altered_degrees(),
                serializer=lambda s: [d.name for d in sorted(s, key=lambda x: x.value)],
            ),
            Field(
                spec=_spec(
                    key="tonal_semitone_tendencies",
                    group=FieldGroup.EVIDENCE,
                    title="tonal semitone tendencies (target=absolute pitch class)",
                    typ=dict,
                    source=FieldSource.HIT,
                    jsonable=True,
                ),
                getter=lambda _: hit.tonal_semitone_tendencies(),
                serializer=lambda d: {k.name: v for k, v in d.items()},
            ),
            Field(
                spec=_spec(
                    key="function_scores",
                    group=FieldGroup.ANALYSIS,
                    title="function scores",
                    typ=dict,
                    source=FieldSource.ANALYSIS,
                    jsonable=True,
                ),
                getter=lambda _: {k.name: v for k, v in self.function_scores.items()},
            ),
            Field(
                spec=_spec(
                    key="function_tendencies",
                    group=FieldGroup.ANALYSIS,
                    title="next function tendencies",
                    typ=dict,
                    source=FieldSource.ANALYSIS,
                    jsonable=True,
                ),
                getter=lambda _: {k.name: v for k, v in self.function_tendencies.items()},
            ),
            Field(
                spec=_spec(
                    key="chromatic_score",
                    group=FieldGroup.ANALYSIS,
                    title="chromatic score",
                    typ=float,
                    source=FieldSource.ANALYSIS,
                    jsonable=True,
                ),
                getter=lambda _: self.chromatic_score,
            ),
        ]
        return AnalysisView(self, fields)
