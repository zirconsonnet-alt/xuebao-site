from ._lookup import LookupEnum


ORDER = ("C", "D", "E", "F", "G", "A", "B")


class Degrees(LookupEnum):
    I = 1
    II = 2
    III = 3
    IV = 4
    V = 5
    VI = 6
    VII = 7

    def __sub__(self, other: "Degrees") -> "Degrees":
        difference = (self.value - other.value + 1) % 7
        if difference == 0:
            difference = 7
        return Degrees(difference)

    def __add__(self, other: "Degrees") -> "Degrees":
        new_value = (self.value + other.value - 1) % 7
        if new_value == 0:
            new_value = 7
        return Degrees(new_value)


class NoteNames(LookupEnum):
    C = 0
    D = 2
    E = 4
    F = 5
    G = 7
    A = 9
    B = 11

    def __sub__(self, other: Degrees) -> "NoteNames":
        self_degree = Degrees(ORDER.index(self.name) + 1)
        other_degree = self_degree - other
        return NoteNames[ORDER[other_degree.value - 1]]

    def __add__(self, other: Degrees) -> "NoteNames":
        self_degree = Degrees(ORDER.index(self.name) + 1)
        other_degree = self_degree + other
        return NoteNames[ORDER[other_degree.value - 1]]

    def __or__(self, other: "NoteNames") -> Degrees:
        self_degree = Degrees(ORDER.index(self.name) + 1)
        other_degree = Degrees(ORDER.index(other.name) + 1)
        return self_degree - other_degree


class Intervals(LookupEnum):
    d1 = (Degrees.I, 11)
    P1 = (Degrees.I, 0)
    A1 = (Degrees.I, 1)
    m2 = (Degrees.II, 1)
    M2 = (Degrees.II, 2)
    A2 = (Degrees.II, 3)
    m3 = (Degrees.III, 3)
    M3 = (Degrees.III, 4)
    d4 = (Degrees.IV, 4)
    P4 = (Degrees.IV, 5)
    A4 = (Degrees.IV, 6)
    d5 = (Degrees.V, 6)
    P5 = (Degrees.V, 7)
    A5 = (Degrees.V, 8)
    d6 = (Degrees.VI, 7)
    m6 = (Degrees.VI, 8)
    M6 = (Degrees.VI, 9)
    A6 = (Degrees.VI, 10)
    d7 = (Degrees.VII, 9)
    m7 = (Degrees.VII, 10)
    M7 = (Degrees.VII, 11)

    @property
    def degree(self) -> Degrees:
        return self.value[0]

    @property
    def semitones(self) -> int:
        return self.value[1]

    def __add__(self, other: "Intervals") -> "Intervals":
        new_degree = self.degree + other.degree
        new_semitones = (self.semitones + other.semitones) % 12
        return Intervals.get((new_degree, new_semitones))

    def __sub__(self, other: "Intervals") -> "Intervals":
        new_degree = self.degree - other.degree
        new_semitones = (self.semitones - other.semitones) % 12
        return Intervals.get((new_degree, new_semitones))
