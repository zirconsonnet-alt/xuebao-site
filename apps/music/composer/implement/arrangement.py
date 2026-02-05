# Module for arrangement
from typing import Dict, Optional
from .note import Note
from ..domain.enums.runtime import Voices


class Arrangement:
    __slots__ = ("note_dict",)

    def __init__(self):
        self.note_dict: Dict[Voices, Optional[Note]] = {
            Voices.Bass: None,
            Voices.Tenor: None,
            Voices.Alto: None,
            Voices.Soprano: None
        }

    def __getitem__(self, item: Voices) -> Optional[Note]:
        return self.note_dict[item]

    def __setitem__(self, item: Voices, value: Optional[Note]) -> None:
        self.note_dict[item] = value

    def __str__(self) -> str:
        return (
            f"{Voices.Bass.value}-{self.note_dict[Voices.Bass]};"
            f"{Voices.Tenor.value}-{self.note_dict[Voices.Tenor]};"
            f"{Voices.Alto.value}-{self.note_dict[Voices.Alto]};"
            f"{Voices.Soprano.value}-{self.note_dict[Voices.Soprano]};"
        )
