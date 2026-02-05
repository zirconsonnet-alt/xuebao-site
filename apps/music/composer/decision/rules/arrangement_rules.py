# Rule checks for arrangement rules
from typing import Dict, List

from ...domain.enums.runtime import LeadingType, Voices
from ...implement import Note


class ArrangementRuleChecker:
    @staticmethod
    def no_voice_crossing(notes: Dict[Voices, Note]) -> bool:
        voice_order = [Voices.Bass, Voices.Tenor, Voices.Alto, Voices.Soprano]
        existing_voices = [v for v in voice_order if v in notes]
        for i in range(1, len(existing_voices)):
            prev = existing_voices[i - 1]
            curr = existing_voices[i]
            if notes[prev].height >= notes[curr].height:
                return False
        return True

    @staticmethod
    def no_min_9th(notes: Dict[Voices, Note]) -> bool:
        existing_notes = list(notes.values())
        for i in range(len(existing_notes)):
            for j in range(i + 1, len(existing_notes)):
                diff = abs(existing_notes[i].height - existing_notes[j].height)
                if diff <= 1:
                    continue
                if (diff - 1) % 12 == 0:
                    return False
        return True

    @staticmethod
    def check_arrangement(notes: Dict[Voices, Note]) -> bool:
        return ArrangementRuleChecker.no_voice_crossing(notes) and ArrangementRuleChecker.no_min_9th(notes)

    @staticmethod
    def no_voice_transcending(progression: List[Dict[Voices, Note]]) -> bool:
        if len(progression) < 2:
            return True
        voice_pairs = [
            (Voices.Bass, Voices.Tenor),
            (Voices.Tenor, Voices.Alto),
            (Voices.Alto, Voices.Soprano),
        ]
        prev_notes = progression[-2]
        curr_notes = progression[-1]
        for lower, higher in voice_pairs:
            if higher in prev_notes and lower in curr_notes:
                if prev_notes[higher].height <= curr_notes[lower].height:
                    return False
            if lower in prev_notes and higher in curr_notes:
                if prev_notes[lower].height >= curr_notes[higher].height:
                    return False
        return True

    @staticmethod
    def no_parallel_5ths(progression: List[Dict[Voices, Note]]) -> bool:
        if len(progression) < 2:
            return True
        for prev_notes, curr_notes in zip(progression[:-1], progression[1:]):
            voices = list(prev_notes.keys())
            pairs = [(v1, v2) for i, v1 in enumerate(voices) for v2 in voices[i + 1:]]
            for v1, v2 in pairs:
                prev_diff = abs(prev_notes[v1].height - prev_notes[v2].height) % 12
                if prev_diff != 7:
                    continue
                if v1 in curr_notes and v2 in curr_notes:
                    curr_diff = abs(curr_notes[v1].height - curr_notes[v2].height) % 12
                    if curr_diff == 7:
                        return False
        return True

    @staticmethod
    def no_parallel_8ves(progression: List[Dict[Voices, Note]]) -> bool:
        if len(progression) < 2:
            return True
        for prev_notes, curr_notes in zip(progression[:-1], progression[1:]):
            voices = list(prev_notes.keys())
            pairs = [(v1, v2) for i, v1 in enumerate(voices) for v2 in voices[i + 1:]]
            for v1, v2 in pairs:
                prev_diff = abs(prev_notes[v1].height - prev_notes[v2].height) % 12
                if prev_diff != 0:
                    continue
                if v1 in curr_notes and v2 in curr_notes:
                    curr_diff = abs(curr_notes[v1].height - curr_notes[v2].height) % 12
                    if curr_diff == 0:
                        return False
        return True

    @staticmethod
    def no_unison_motion(progression: List[Dict[Voices, Note]]) -> bool:
        if len(progression) < 2:
            return True
        required_voices = {Voices.Bass, Voices.Tenor, Voices.Alto, Voices.Soprano}
        for prev_notes, curr_notes in zip(progression[:-1], progression[1:]):
            if not (required_voices.issubset(prev_notes) and required_voices.issubset(curr_notes)):
                continue
            deltas = [curr_notes[v].height - prev_notes[v].height for v in required_voices]
            if all(d > 0 for d in deltas) or all(d < 0 for d in deltas):
                return False
        return True

    @staticmethod
    def check_progression(progression: List[Dict[Voices, Note]]) -> bool:
        return (
            ArrangementRuleChecker.no_voice_transcending(progression)
            and ArrangementRuleChecker.no_parallel_5ths(progression)
            and ArrangementRuleChecker.no_parallel_8ves(progression)
            and ArrangementRuleChecker.no_unison_motion(progression)
        )
