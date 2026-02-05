# Analysis explanations for chord in mode
from dataclasses import dataclass
from typing import Dict, Set
from ...core.hits.chord_in_mode import ChordInModeHit
from ....domain.enums.harmony import Functions
from ....domain.enums.runtime import TurningPoints
from ..view import AnalysisView, Field, FieldGroup, FieldSource, FieldSpec


@dataclass(frozen=True, slots=True)
class ChordInModeAnalysis:
    hit: ChordInModeHit

    turning_points: Set[TurningPoints]

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
                    key="turning_points",
                    group=FieldGroup.EVIDENCE,
                    title="turning points",
                    typ=Set[TurningPoints],
                    source=FieldSource.HIT,
                ),
                getter=lambda _: hit.turning_points(),
            ),
            Field(
                spec=_spec(
                    key="function_scores",
                    group=FieldGroup.ANALYSIS,
                    title="function scores",
                    typ=Dict[Functions, float],
                    source=FieldSource.ANALYSIS,
                ),
                getter=lambda _: self.function_scores,
            ),
            Field(
                spec=_spec(
                    key="function_tendencies",
                    group=FieldGroup.ANALYSIS,
                    title="next function tendencies",
                    typ=Dict[Functions, float],
                    source=FieldSource.ANALYSIS,
                ),
                getter=lambda _: self.function_tendencies,
            ),
            Field(
                spec=_spec(
                    key="chromatic_score",
                    group=FieldGroup.ANALYSIS,
                    title="chromatic",
                    typ=float,
                    source=FieldSource.ANALYSIS,
                ),
                getter=lambda _: self.chromatic_score,
            ),
        ]
        return AnalysisView(self, fields)

    def __str__(self) -> str:
        func_items = sorted(self.function_scores.items(), key=lambda kv: kv[1], reverse=True)
        function_str = ", ".join(f"{f.name}={score:.2f}" for f, score in func_items if score != 0.0) or "None"
        if self.turning_points:
            tp_str = ", ".join(sorted(tp.name for tp in self.turning_points))
        else:
            tp_str = "None"
        tend_items = sorted(self.function_tendencies.items(), key=lambda kv: kv[1], reverse=True)
        tendency_str = ", ".join(f"{f.name}={score:.2f}" for f, score in tend_items if score != 0.0) or "None"
        return (
            f"ChordInModeAnalysis(chord={self.hit.chord},\n"
            f"variant={self.hit.chord_id.variant.name},\n"
            f"functions=[{function_str}],\n"
            f"turning_points=[{tp_str}],\n"
            f"next_function_tendencies=[{tendency_str}],\n"
            f"chromatic={self.chromatic_score:.2f})"
        )
