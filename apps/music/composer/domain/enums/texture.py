from enum import auto
from ._lookup import LookupEnum


class Textures(LookupEnum):
    Columnar = "columnar"
    Ascending = "ascending"
    Triangular = "triangular"
    Decomposition = "decomposition"
