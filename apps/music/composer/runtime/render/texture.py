# Rendering utilities for texture
from typing import List, Dict, Any
from ...domain.enums.runtime import Voices
from ...domain.enums.texture import Textures
from ..implement import Arrangement


class TextureGenerator:
    COLOR: Dict[Voices, int] = {
        Voices.Bass: 1,
        Voices.Tenor: 5,
        Voices.Alto: 9,
        Voices.Soprano: 13,
    }

    def __init__(self, texture: Textures = Textures.Columnar):
        self.texture = texture

    def generate(self, arrangement_list: List[Arrangement], duration: int = 1920, velocity: int = 48) \
            -> List[List[Dict[str, Any]]]:
        textures: List[List[Dict[str, Any]]] = []
        for arrangement in arrangement_list:
            textures.append(self.generate_texture(arrangement, duration, velocity))
        return textures

    def generate_texture(self, arrangement: Arrangement, duration: int = 1920, velocity: int = 48) \
            -> List[Dict[str, Any]]:
        if self.texture == Textures.Columnar:
            return self._columnar(arrangement, duration, velocity)
        elif self.texture == Textures.Decomposition:
            return self._decomposition(arrangement, duration, velocity)
        else:
            raise ValueError(f"不支持的纹理类型: {self.texture}")

    @staticmethod
    def _iter_notes(arrangement: Arrangement) -> List[tuple[Voices, Any]]:
        items: List[tuple[Voices, Any]] = []
        for voice, note in arrangement.note_dict.items():
            if note is None:
                continue
            items.append((voice, note))
        return items

    def _columnar(self, arrangement: Arrangement, duration: int, velocity: int) -> List[Dict[str, Any]]:
        texture: List[Dict[str, Any]] = []
        for voice, note in self._iter_notes(arrangement):
            color = self.COLOR.get(voice, 0)
            texture.append({
                "note": note,
                "start_time": 0,
                "duration": duration,
                "velocity": velocity,
                "color": color,
            })
        return texture

    def _decomposition(self, arrangement: Arrangement, duration: int, velocity: int) -> List[Dict[str, Any]]:
        notes = self._iter_notes(arrangement)
        if not notes:
            return []
        step = max(1, duration // len(notes))
        texture: List[Dict[str, Any]] = []
        for i, (voice, note) in enumerate(notes):
            color = self.COLOR.get(voice, 0)
            texture.append({
                "note": note,
                "start_time": i * step,
                "duration": duration - i * step,
                "velocity": velocity,
                "color": color,
            })
        return texture
