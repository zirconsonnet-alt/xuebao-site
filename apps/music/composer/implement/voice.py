# Module for voice
from typing import Dict, Callable, Generator
from ..domain import Chord
from .note import Note
from ..domain.enums.core import Degrees, Intervals
from ..domain.enums.runtime import LeadingType, States


class Voice:
    _TRANSITION_RULES: Dict[LeadingType, States] = {
        LeadingType.Step: States.Consonant,
        LeadingType.Jump: States.Consonant,
        LeadingType.Suspend: States.Dissonant,
        LeadingType.Transit: States.Dissonant,
    }

    def __init__(self, start: Note):
        self.state_stack = [States.Consonant]
        self.note_list = [start]
        self.limit = (start.height - 12, start.height + 12)
        self.leading_type_to_method: Dict[LeadingType, Callable[[Chord], Generator[Note, None, None]]] = {
            LeadingType.Step: self._step,
            LeadingType.Jump: self._jump,
            LeadingType.Transit: self._transit,
            LeadingType.Suspend: self._suspend,
        }

    @property
    def state(self) -> States:
        return self.state_stack[-1]

    def lead(self, lt: LeadingType, chord: Chord) -> Generator[Note, None, None]:
        yield from self.leading_type_to_method[lt](chord)

    def forward(self, note: Note, lt: LeadingType) -> None:
        new_state = Voice._TRANSITION_RULES[lt]
        self.state_stack.append(new_state)
        self.note_list.append(note)

    def backward(self) -> None:
        if len(self.note_list) <= 1:
            return
        if len(self.state_stack) > 1:
            self.state_stack.pop()
        self.note_list.pop()

    def _step(self, chord: Chord) -> Generator[Note, None, None]:
        this_note = self.note_list[-1]
        for chord_tone in chord():
            for octave_delta in (-1, 0, 1):
                next_note = Note(chord_tone, this_note.octave + octave_delta)
                interval: Intervals = this_note.base_note | next_note.base_note
                degree_diff: Degrees = interval.value[0]
                distance = abs(this_note.height - next_note.height)
                if (
                    degree_diff in (Degrees.II, Degrees.VII)
                    and distance <= 2
                    and self.limit[0] < next_note.height < self.limit[1]
                ):
                    yield next_note

    def _jump(self, chord: Chord) -> Generator[Note, None, None]:
        if self.state == States.Dissonant:
            return
        this_note = self.note_list[-1]
        for chord_tone in chord():
            for octave_delta in (-1, 0, 1):
                next_note = Note(chord_tone, this_note.octave + octave_delta)
                interval: Intervals = this_note.base_note | next_note.base_note
                degree_diff: Degrees = interval.value[0]
                distance = abs(this_note.height - next_note.height)
                if (
                    degree_diff not in (Degrees.II, Degrees.VII)
                    and distance <= 12
                    and self.limit[0] < next_note.height < self.limit[1]
                ):
                    yield next_note

    def _suspend(self, chord: Chord) -> Generator[Note, None, None]:
        if self.state == States.Dissonant:
            return
        this_note = self.note_list[-1]
        deg_in_scale = chord.scale | this_note.base_note
        if deg_in_scale is None:
            return
        rel = chord | deg_in_scale
        if rel is None:
            return
        if rel in (Degrees.II, Degrees.IV, Degrees.VI, Degrees.VII):
            yield this_note

    def _transit(self, chord: Chord) -> Generator[Note, None, None]:
        if self.state == States.Dissonant:
            return
        this_note = self.note_list[-1]
        for scale_tone in chord.scale.note_list:
            for octave_delta in (-1, 0, 1):
                next_note = Note(scale_tone, this_note.octave + octave_delta)
                interval: Intervals = this_note.base_note | next_note.base_note
                degree_diff: Degrees = interval.value[0]
                distance = abs(this_note.height - next_note.height)
                deg_in_scale = chord.scale | next_note.base_note
                if deg_in_scale is None:
                    continue
                rel = chord | deg_in_scale
                if rel is None:
                    continue
                dissonant = rel in (Degrees.II, Degrees.IV, Degrees.VI, Degrees.VII)
                if (
                    degree_diff in (Degrees.II, Degrees.VII)
                    and distance <= 2
                    and dissonant
                    and self.limit[0] < next_note.height < self.limit[1]
                ):
                    yield next_note
