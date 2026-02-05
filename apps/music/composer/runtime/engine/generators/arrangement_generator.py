# Generator module for arrangement generator
import random
from typing import List, Dict, Optional, Tuple, Iterable
from ....domain.enums.core import Degrees
from ....domain.enums.runtime import Voices, LeadingType
from ....domain import Chord
from ....domain.relations import ChordInfo
from ....implement import Voice, Note, Arrangement
from ....decision.rules.arrangement_rules import ArrangementRuleChecker


class ArrangementGenerator:
    def __init__(self, chord_list: Iterable[Chord] | Iterable[ChordInfo], *, rng: Optional[random.Random] = None):
        chords = self._coerce_chords(chord_list)
        if not chords:
            raise ValueError("chord_list 不能为空")
        self.chord_list = chords
        self.rng = rng or random.Random()
        self.max_depth = 2000
        c0 = chords[0]
        root = c0[Degrees.I]
        third = c0[Degrees.III]
        fifth = c0[Degrees.V]
        start_frame: Dict[Voices, Note] = {
            Voices.Bass: Note(root, 4),
            Voices.Tenor: Note(fifth, 4),
            Voices.Alto: Note(root, 5),
            Voices.Soprano: Note(third, 5),
        }
        self.start_frame = start_frame
        self.voices: List[Tuple[Voices, Voice]] = [
            (Voices.Bass, Voice(start_frame[Voices.Bass])),
            (Voices.Tenor, Voice(start_frame[Voices.Tenor])),
            (Voices.Alto, Voice(start_frame[Voices.Alto])),
            (Voices.Soprano, Voice(start_frame[Voices.Soprano])),
        ]
        self.leading_types: Tuple[LeadingType, ...] = (
            LeadingType.Step,
            LeadingType.Jump,
            LeadingType.Suspend,
            LeadingType.Transit,
        )
        self.voice_order: Tuple[Voices, ...] = (
            Voices.Bass,
            Voices.Soprano,
            Voices.Tenor,
            Voices.Alto,
        )
        self.voice_index: Dict[Voices, int] = {v: i for i, v in enumerate(self.voice_order)}
        self.voice_map: Dict[Voices, Voice] = {v: obj for v, obj in self.voices}

    @staticmethod
    def _coerce_chords(items: Iterable[Chord] | Iterable[ChordInfo]) -> List[Chord]:
        items = list(items)
        if not items:
            return []
        first = items[0]
        if isinstance(first, Chord):
            return list(items)
        if isinstance(first, tuple):
            key_id, _, _ = first
            key = key_id.resolve()
            chords: List[Chord] = []
            for t in items:
                if t[0] != key_id:
                    raise ValueError("ChordInfo 的 key 身份不一致，无法生成和弦序列")
                _, mode_id, chord_id = t
                mode = mode_id.resolve(key)
                chord = chord_id.resolve(mode)
                chords.append(chord)
            return chords
        raise TypeError("arrangement_generator 仅接受 Chord 或 ChordInfo 列表")

    def generate(self) -> Optional[List[Arrangement]]:
        progression = [self.start_frame.copy()]
        result = self._backtrack_progression(progression, idx=1, depth=0)
        if result is None:
            return None
        arrangements: List[Arrangement] = []
        for note_dict in result:
            arr = Arrangement()
            for voice, note in note_dict.items():
                arr[voice] = note
            arrangements.append(arr)
        return arrangements

    def _backtrack_progression(
        self,
        progression: List[Dict[Voices, Note]],
        idx: int,
        depth: int,
    ) -> Optional[List[Dict[Voices, Note]]]:
        if idx >= len(self.chord_list):
            return progression
        if depth > self.max_depth:
            return None
        chord = self.chord_list[idx]
        arrangements = self._backtrack_arrangement_for_chord(chord)
        for arrangement in arrangements:
            progression.append(arrangement)
            if ArrangementRuleChecker.check_progression(progression):
                result = self._backtrack_progression(progression, idx + 1, depth + 1)
                if result is not None:
                    return result
            progression.pop()
        return None

    def _backtrack_arrangement_for_chord(self, chord: Chord) -> List[Dict[Voices, Note]]:
        target_tones = {bn for bn in chord.base_notes}

        def _iter_sorted_candidates(voice: Voice, lt: LeadingType) -> List[Note]:
            candidates = [n for n in voice.lead(lt, chord) if n is not None]
            last_h = voice.note_list[-1].height
            candidates.sort(key=lambda x: abs(x.height - last_h))
            return candidates

        def _has_chord_coverage(notes: Dict[Voices, Note]) -> bool:
            bases = {n.base_note for n in notes.values()}
            return target_tones.issubset(bases)

        def _backtrack_voice_k(k: int, notes: Dict[Voices, Note], out: List[Dict[Voices, Note]]) -> None:
            if k == len(self.voice_order):
                if _has_chord_coverage(notes):
                    out.append(notes.copy())
                return
            v = self.voice_order[k]
            voice_obj = self.voice_map[v]
            leading_types = list(self.leading_types)
            self.rng.shuffle(leading_types)
            for lt in leading_types:
                candidates = _iter_sorted_candidates(voice_obj, lt)
                for n in candidates:
                    voice_obj.forward(n, lt)
                    notes[v] = n
                    if ArrangementRuleChecker.check_arrangement(notes):
                        _backtrack_voice_k(k + 1, notes, out)
                    voice_obj.backward()
                    del notes[v]
        results: List[Dict[Voices, Note]] = []
        _backtrack_voice_k(0, {}, results)
        return results
