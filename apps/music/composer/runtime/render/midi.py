# Rendering utilities for midi
import io
import os
import platform
import subprocess
from pathlib import Path
from typing import List, Dict, Union, Tuple
from pydub import AudioSegment
from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo
from ..implement import Note


EventDict = Dict[str, Union[Note, int]]


class MidiGenerator:
    def __init__(self, tempo: int = 120, ticks_per_beat: int = 480):
        self.tempo = tempo
        self.ticks_per_beat = ticks_per_beat
        self._reset()

    def _reset(self) -> None:
        self.midi_file = MidiFile(ticks_per_beat=self.ticks_per_beat)
        self.track = MidiTrack()
        self.midi_file.tracks.append(self.track)
        self.track.append(MetaMessage("set_tempo", tempo=bpm2tempo(self.tempo), time=0))

    @staticmethod
    def _safe_channel(value: int) -> int:
        # MIDI channel 必须 0~15
        if not isinstance(value, int):
            return 0
        return max(0, min(15, value))

    def _build_events(self, texture_list: List[List[EventDict]], measure_duration: int) \
            -> List[Tuple[str, int, int, int, int]]:
        events: List[Tuple[str, int, int, int, int]] = []
        for measure_idx, per_measure in enumerate(texture_list):
            base_tick = measure_idx * measure_duration
            for t in per_measure:
                note = t.get("note")
                if note is None:
                    continue
                if not isinstance(note, Note):
                    raise TypeError(f"texture event.note 必须为 Note, got {type(note)}")
                start = int(t.get("start_time", 0)) + base_tick
                dur = int(t.get("duration", 0))
                vel = int(t.get("velocity", 64))
                chan = self._safe_channel(int(t.get("color", 0)))
                if dur <= 0:
                    continue
                end = start + dur
                pitch = note.height
                events.append(("note_on", pitch, vel, start, chan))
                events.append(("note_off", pitch, 0, end, chan))
        events.sort(key=lambda x: (x[3], 0 if x[0] == "note_off" else 1, x[1]))
        return events

    def _write_events(self, events: List[Tuple[str, int, int, int, int]]) -> None:
        if not events:
            return
        last_tick = 0
        for msg_type, pitch, velocity, tick, channel in events:
            delta = tick - last_tick
            if delta < 0:
                raise ValueError("事件时间倒流：请检查排序或 start_time/duration")
            self.track.append(Message(msg_type, note=pitch, velocity=velocity, time=delta, channel=channel))
            last_tick = tick

    def generate(
        self,
        texture_list: List[List[EventDict]],
        measure_duration: int = 1920,
        output_mid: str = r"output\output.mid",
        export_mp3: bool = True
    ) -> str:
        self._reset()
        events = self._build_events(texture_list, measure_duration)
        self._write_events(events)
        out_path = Path(output_mid)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        self.midi_file.save(out_path)
        if not export_mp3:
            return str(out_path)
        wav_path = self._midi_to_wav(str(out_path))
        mp3_path = self._wav_to_mp3(wav_path)
        return mp3_path

    def generate_midi_bytes(
        self,
        texture_list: List[List[EventDict]],
        measure_duration: int = 1920
    ) -> bytes:
        self._reset()
        events = self._build_events(texture_list, measure_duration)
        self._write_events(events)
        buffer = io.BytesIO()
        self.midi_file.save(file=buffer)
        return buffer.getvalue()

    @staticmethod
    def _midi_to_wav(midi_filename: str) -> str:
        soundfont = r"data\soundfont.sf2"
        wav_filename = str(Path(midi_filename).with_suffix(".wav"))
        system = platform.system().lower()
        command = [r"fluidsynth", "-ni", soundfont, midi_filename, "-F", wav_filename, "-g", "1.0"]
        if system == "linux":
            command += ["-a", "alsa"]
        elif system == "darwin":
            pass
        else:
            pass
        subprocess.run(command, check=True)
        return wav_filename

    @staticmethod
    def _wav_to_mp3(wav_filename: str) -> str:
        mp3_filename = str(Path(wav_filename).with_suffix(".mp3"))
        mp3_filepath = os.path.abspath(mp3_filename)
        audio = AudioSegment.from_wav(wav_filename)
        audio.export(mp3_filepath, format="mp3")
        return mp3_filepath
