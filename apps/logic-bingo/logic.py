from __future__ import annotations

import random
from abc import ABC, abstractmethod
from enum import Enum
from typing import Generator, List, Optional, Set, Tuple

import numpy as np
from numpy._typing import NDArray


class LineType(Enum):
    ROW = "行"
    COLUMN = "列"
    DIAGONAL = "对角线"


class PositionIndex(Enum):
    I = 0
    II = 1
    III = 2
    IV = 3
    V = 4
    SELF = "该格所在"


class DiagonalType(Enum):
    AUTO = "该格所在对角线"
    BOTH = "双对角线"
    MAIN = "主对角线"
    ANTI = "副对角线"
    NONE = ""


class ComparisonType(Enum):
    EQUAL = "等于"
    LESS_EQUAL = "小于等于"
    GREATER_EQUAL = "大于等于"
    LESS = "小于"
    GREATER = "大于"


class ExtremeType(Enum):
    MIN = "最少"
    MAX = "最多"


class SubMatrixType(Enum):
    ONES = "全1"
    ZEROS = "全0"


class Sentence(ABC):
    PARAM_TYPES: List
    UNIQUE: bool
    UNIQUE_ID: bool

    def __init__(self, position: Tuple[int, int]):
        self.position = position

    @abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def unique_id(self):
        raise NotImplementedError

    @abstractmethod
    def execute(self, matrix: NDArray[np.int_]) -> int:
        raise NotImplementedError

    @abstractmethod
    def execute_partial(self, matrix: NDArray[np.int_]) -> Tuple[bool, bool]:
        raise NotImplementedError


class ChooseThis(Sentence):
    PARAM_TYPES: List = []
    UNIQUE = False
    UNIQUE_ID = False

    def __str__(self) -> str:
        return "这个格子打勾"

    @property
    def unique_id(self):
        return None

    def execute(self, matrix: NDArray[np.int_]) -> int:
        r, c = self.position
        return int(matrix[r, c])

    def execute_partial(self, matrix: NDArray[np.int_]) -> Tuple[bool, bool]:
        r, c = self.position
        value = matrix[r, c]
        if value in [0, 1]:
            return value == 1, value == 0
        return True, True


class LineFull(Sentence):
    PARAM_TYPES: List = [PositionIndex, LineType]
    UNIQUE = False
    UNIQUE_ID = True

    def __init__(self, position, line_number: PositionIndex, axis: LineType):
        super().__init__(position)
        if axis == LineType.DIAGONAL:
            raise ValueError("Diagonal lines should use DiagonalFull.")
        self.line_number = line_number
        self.axis = axis
        if self.line_number == PositionIndex.SELF:
            if self.axis == LineType.ROW:
                self.normalized_line_number = PositionIndex(self.position[0])
            else:
                self.normalized_line_number = PositionIndex(self.position[1])
        else:
            self.normalized_line_number = self.line_number
        self._unique_id = (self.__class__.__name__, self.normalized_line_number, self.axis.value)

    def __str__(self) -> str:
        prefix = "该格所在" if self.line_number == PositionIndex.SELF else f"第{self.line_number.value + 1}"
        return f"{prefix}{self.axis.value}可连成一线"

    @property
    def unique_id(self):
        return self._unique_id

    def execute(self, matrix: NDArray[np.int_]) -> int:
        line_to_check = self.normalized_line_number.value
        if self.axis == LineType.ROW:
            return 1 if np.all(matrix[line_to_check, :] == 1) else 0
        if self.axis == LineType.COLUMN:
            return 1 if np.all(matrix[:, line_to_check] == 1) else 0
        return 0

    def execute_partial(self, matrix: NDArray[np.int_]) -> Tuple[bool, bool]:
        line_to_check = self.normalized_line_number.value
        if self.axis == LineType.ROW:
            row = matrix[line_to_check, :]
            possible_true = np.all(row != 0)
            possible_false = np.any(row == 0)
        elif self.axis == LineType.COLUMN:
            col = matrix[:, line_to_check]
            possible_true = np.all(col != 0)
            possible_false = np.any(col == 0)
        else:
            return True, True
        return possible_true, possible_false


class DiagonalFull(Sentence):
    PARAM_TYPES: List = [DiagonalType]
    UNIQUE = False
    UNIQUE_ID = True

    def __init__(self, position, diag_type: DiagonalType):
        super().__init__(position)
        self.diag_type = diag_type
        if self.diag_type == DiagonalType.AUTO:
            n = 5
            r, c = self.position
            if r == c and r + c == n - 1:
                self.normalized_diag_type = DiagonalType.BOTH
            elif r == c:
                self.normalized_diag_type = DiagonalType.MAIN
            elif r + c == n - 1:
                self.normalized_diag_type = DiagonalType.ANTI
            else:
                raise ValueError
        else:
            self.normalized_diag_type = self.diag_type
        self._unique_id = (self.__class__.__name__, self.normalized_diag_type)

    def __str__(self) -> str:
        return f"{self.diag_type.value}可连成一线"

    @property
    def unique_id(self):
        return self._unique_id

    def execute(self, matrix: NDArray[np.int_]) -> int:
        n = matrix.shape[0]
        r, c = self.position
        if self.diag_type == DiagonalType.AUTO:
            on_main_diag = r == c
            on_anti_diag = r + c == n - 1
            if not (on_main_diag or on_anti_diag):
                return 0
            main_diag_full = True
            if on_main_diag:
                main_diag_full = np.all(np.diag(matrix) == 1)
            anti_diag_full = True
            if on_anti_diag:
                anti_diag_full = np.all(np.diag(np.fliplr(matrix)) == 1)
            if on_main_diag and on_anti_diag:
                return 1 if (main_diag_full and anti_diag_full) else 0
            if on_main_diag:
                return 1 if main_diag_full else 0
            return 1 if anti_diag_full else 0
        if self.diag_type == DiagonalType.MAIN:
            return 1 if np.all(np.diag(matrix) == 1) else 0
        if self.diag_type == DiagonalType.ANTI:
            return 1 if np.all(np.diag(np.fliplr(matrix)) == 1) else 0
        return 0

    def execute_partial(self, matrix: NDArray[np.int_]) -> Tuple[bool, bool]:
        n = matrix.shape[0]
        r, c = self.position
        if self.diag_type == DiagonalType.AUTO:
            on_main_diag = r == c
            on_anti_diag = r + c == n - 1
            if not (on_main_diag or on_anti_diag):
                return False, True
            main_possible_true, main_possible_false = True, False
            anti_possible_true, anti_possible_false = True, False
            if on_main_diag:
                main_diag = np.diag(matrix)
                main_possible_true = np.all(main_diag != 0)
                main_possible_false = np.any(main_diag == 0)
            if on_anti_diag:
                anti_diag = np.diag(np.fliplr(matrix))
                anti_possible_true = np.all(anti_diag != 0)
                anti_possible_false = np.any(anti_diag == 0)
            if on_main_diag and on_anti_diag:
                possible_true = main_possible_true and anti_possible_true
                possible_false = main_possible_false or anti_possible_false
            elif on_main_diag:
                possible_true = main_possible_true
                possible_false = main_possible_false
            else:
                possible_true = anti_possible_true
                possible_false = anti_possible_false
        elif self.diag_type == DiagonalType.MAIN:
            diag = np.diag(matrix)
            possible_true = np.all(diag != 0)
            possible_false = np.any(diag == 0)
        elif self.diag_type == DiagonalType.ANTI:
            diag = np.diag(np.fliplr(matrix))
            possible_true = np.all(diag != 0)
            possible_false = np.any(diag == 0)
        else:
            return True, True
        return possible_true, possible_false


class HowMany(Sentence):
    PARAM_TYPES: List = [(5, 17), ComparisonType]
    UNIQUE = False
    UNIQUE_ID = False

    def __init__(self, position: Tuple[int, int], number: int, comp_type: ComparisonType):
        super().__init__(position)
        self.number = number
        self.comp_type = comp_type

    def __str__(self) -> str:
        return f"打勾格子总数{self.comp_type.value}{self.number}"

    @property
    def unique_id(self):
        return None

    def execute(self, matrix: NDArray[np.int_]) -> int:
        ones_count = np.sum(matrix == 1)
        if self.comp_type == ComparisonType.EQUAL:
            return 1 if ones_count == self.number else 0
        if self.comp_type == ComparisonType.LESS_EQUAL:
            return 1 if ones_count <= self.number else 0
        if self.comp_type == ComparisonType.GREATER_EQUAL:
            return 1 if ones_count >= self.number else 0
        if self.comp_type == ComparisonType.LESS:
            return 1 if ones_count < self.number else 0
        if self.comp_type == ComparisonType.GREATER:
            return 1 if ones_count > self.number else 0
        return 0

    def execute_partial(self, matrix: NDArray[np.int_]) -> Tuple[bool, bool]:
        return True, True


class NeighborhoodCount(Sentence):
    PARAM_TYPES: List = [(0, 8), ComparisonType]
    UNIQUE = False
    UNIQUE_ID = False

    def __init__(self, position, number: int, comp_type: ComparisonType):
        super().__init__(position)
        self.number = number
        self.comp_type = comp_type

    def __str__(self) -> str:
        return f"该格周围打勾格子总数{self.comp_type.value}{self.number}"

    @property
    def unique_id(self):
        return None

    def execute(self, matrix: NDArray[np.int_]) -> int:
        r, c = self.position
        n = matrix.shape[0]
        dr = [-1, -1, -1, 0, 0, 1, 1, 1]
        dc = [-1, 0, 1, -1, 1, -1, 0, 1]
        count = 0
        for i in range(8):
            nr, nc = r + dr[i], c + dc[i]
            if 0 <= nr < n and 0 <= nc < n and matrix[nr, nc] == 1:
                count += 1
        if self.comp_type == ComparisonType.EQUAL:
            return 1 if count == self.number else 0
        if self.comp_type == ComparisonType.GREATER_EQUAL:
            return 1 if count >= self.number else 0
        if self.comp_type == ComparisonType.LESS_EQUAL:
            return 1 if count <= self.number else 0
        if self.comp_type == ComparisonType.GREATER:
            return 1 if count > self.number else 0
        if self.comp_type == ComparisonType.LESS:
            return 1 if count < self.number else 0
        return 0

    def execute_partial(self, matrix: NDArray[np.int_]) -> Tuple[bool, bool]:
        return True, True


class ExistsNeighborhoodCount(Sentence):
    PARAM_TYPES: List = [(0, 8), ComparisonType]
    UNIQUE = True
    UNIQUE_ID = False

    def __init__(self, position, number: int, comp_type: ComparisonType):
        super().__init__(position)
        self.number = number
        self.comp_type = comp_type

    def __str__(self) -> str:
        return f"存在格子周围打勾格子总数{self.comp_type.value}{self.number}"

    @property
    def unique_id(self):
        return None

    def execute(self, matrix: NDArray[np.int_]) -> int:
        n = matrix.shape[0]
        dr = [-1, -1, -1, 0, 0, 1, 1, 1]
        dc = [-1, 0, 1, -1, 1, -1, 0, 1]
        for r in range(n):
            for c in range(n):
                count = 0
                for i in range(8):
                    nr, nc = r + dr[i], c + dc[i]
                    if 0 <= nr < n and 0 <= nc < n and matrix[nr, nc] == 1:
                        count += 1
                if self.comp_type == ComparisonType.EQUAL and count == self.number:
                    return 1
                if self.comp_type == ComparisonType.GREATER_EQUAL and count >= self.number:
                    return 1
                if self.comp_type == ComparisonType.LESS_EQUAL and count <= self.number:
                    return 1
                if self.comp_type == ComparisonType.GREATER and count > self.number:
                    return 1
                if self.comp_type == ComparisonType.LESS and count < self.number:
                    return 1
        return 0

    def execute_partial(self, matrix: NDArray[np.int_]) -> Tuple[bool, bool]:
        return True, True


class CenterIsOne(Sentence):
    PARAM_TYPES: List = []
    UNIQUE = True
    UNIQUE_ID = False

    def __str__(self) -> str:
        return "中心格子打勾"

    @property
    def unique_id(self):
        return None

    def execute(self, matrix: NDArray[np.int_]) -> int:
        n = matrix.shape[0]
        center = n // 2
        if n % 2 == 1:
            return 1 if matrix[center, center] == 1 else 0
        return 1 if (
            matrix[center - 1, center - 1] == 1
            or matrix[center - 1, center] == 1
            or matrix[center, center - 1] == 1
            or matrix[center, center] == 1
        ) else 0

    def execute_partial(self, matrix: NDArray[np.int_]) -> Tuple[bool, bool]:
        n = matrix.shape[0]
        if n % 2 == 1:
            center = n // 2
            value = matrix[center, center]
            if value in [0, 1]:
                return value == 1, value == 0
            return True, True
        centers = [
            (n // 2 - 1, n // 2 - 1),
            (n // 2 - 1, n // 2),
            (n // 2, n // 2 - 1),
            (n // 2, n // 2),
        ]
        possible_true = any(matrix[r, c] != 0 for r, c in centers)
        possible_false = all(matrix[r, c] != 1 for r, c in centers)
        return possible_true, possible_false


class CornersCount(Sentence):
    PARAM_TYPES: List = [(0, 4)]
    UNIQUE = True
    UNIQUE_ID = False

    def __init__(self, position, number: int):
        super().__init__(position)
        self.number = number

    def __str__(self) -> str:
        return f"四角恰有{self.number}个格子打勾"

    @property
    def unique_id(self):
        return None

    def execute(self, matrix: NDArray[np.int_]) -> int:
        n = matrix.shape[0]
        corners = [
            matrix[0, 0],
            matrix[0, n - 1],
            matrix[n - 1, 0],
            matrix[n - 1, n - 1],
        ]
        count = sum(1 for corner in corners if corner == 1)
        return 1 if count == self.number else 0

    def execute_partial(self, matrix: NDArray[np.int_]) -> Tuple[bool, bool]:
        return True, True


class LineExtreme(Sentence):
    PARAM_TYPES: List = [PositionIndex, LineType, ExtremeType]
    UNIQUE = False
    UNIQUE_ID = True

    def __init__(self, position, line_number: PositionIndex, axis: LineType, extreme_type: ExtremeType):
        super().__init__(position)
        if axis == LineType.DIAGONAL:
            raise ValueError("Diagonal lines are not supported here.")
        self.line_number = line_number
        self.axis = axis
        self.extreme_type = extreme_type
        if self.line_number == PositionIndex.SELF:
            if self.axis == LineType.ROW:
                self.normalized_line_number = PositionIndex(self.position[0])
            else:
                self.normalized_line_number = PositionIndex(self.position[1])
        else:
            self.normalized_line_number = self.line_number
        self._unique_id = (
            self.__class__.__name__,
            self.normalized_line_number,
            self.axis.value,
            self.extreme_type.value,
        )

    def __str__(self) -> str:
        prefix = "该格所在" if self.line_number == PositionIndex.SELF else f"第{self.line_number.value + 1}"
        return f"{prefix}{self.axis.value}是打勾格子{self.extreme_type.value}的{self.axis.value}"

    @property
    def unique_id(self):
        return self._unique_id

    def execute(self, matrix: NDArray[np.int_]) -> int:
        if self.axis == LineType.ROW:
            counts = np.sum(matrix, axis=1)
        elif self.axis == LineType.COLUMN:
            counts = np.sum(matrix, axis=0)
        else:
            return 0
        target_count = counts[self.normalized_line_number.value]
        if self.extreme_type == ExtremeType.MIN:
            min_count = np.min(counts)
            min_indices = np.where(counts == min_count)[0]
            return 1 if target_count == min_count and len(min_indices) == 1 else 0
        if self.extreme_type == ExtremeType.MAX:
            max_count = np.max(counts)
            max_indices = np.where(counts == max_count)[0]
            return 1 if target_count == max_count and len(max_indices) == 1 else 0
        return 0

    def execute_partial(self, matrix: NDArray[np.int_]) -> Tuple[bool, bool]:
        return True, True


class RowColComparison(Sentence):
    PARAM_TYPES: List = [ComparisonType]
    UNIQUE = False
    UNIQUE_ID = False

    def __init__(self, position, comp_type: ComparisonType):
        super().__init__(position)
        self.comp_type = comp_type

    def __str__(self) -> str:
        return f"该格所在行打勾格子数量{self.comp_type.value}所在列"

    @property
    def unique_id(self):
        return None

    def execute(self, matrix: NDArray[np.int_]) -> int:
        r, c = self.position
        row_count = np.sum(matrix[r, :])
        col_count = np.sum(matrix[:, c])
        if self.comp_type == ComparisonType.GREATER:
            return 1 if row_count > col_count else 0
        if self.comp_type == ComparisonType.LESS:
            return 1 if row_count < col_count else 0
        if self.comp_type == ComparisonType.EQUAL:
            return 1 if row_count == col_count else 0
        if self.comp_type == ComparisonType.GREATER_EQUAL:
            return 1 if row_count >= col_count else 0
        if self.comp_type == ComparisonType.LESS_EQUAL:
            return 1 if row_count <= col_count else 0
        return 0

    def execute_partial(self, matrix: NDArray[np.int_]) -> Tuple[bool, bool]:
        return True, True


class TwoByTwoSubMatrix(Sentence):
    PARAM_TYPES: List = [SubMatrixType]
    UNIQUE = True
    UNIQUE_ID = False

    def __init__(self, position, sub_type: SubMatrixType):
        super().__init__(position)
        self.sub_type = sub_type

    def __str__(self) -> str:
        return f"存在2*2的{self.sub_type.value}矩阵"

    @property
    def unique_id(self):
        return None

    def execute(self, matrix: NDArray[np.int_]) -> int:
        n = matrix.shape[0]
        for i in range(n - 1):
            for j in range(n - 1):
                sub_matrix = matrix[i : i + 2, j : j + 2]
                if self.sub_type == SubMatrixType.ONES and np.all(sub_matrix == 1):
                    return 1
                if self.sub_type == SubMatrixType.ZEROS and np.all(sub_matrix == 0):
                    return 1
        return 0

    def execute_partial(self, matrix: NDArray[np.int_]) -> Tuple[bool, bool]:
        return True, True


class BingoGenerator:
    all_sentence_classes = [cls for cls in Sentence.__subclasses__() if cls != Sentence]

    def __init__(self, number: int = 5):
        self.number = number
        self.matrix: np.ndarray = np.full((self.number, self.number), -1, dtype=int)
        self.generate_special_matrix()
        self.sentences: List[List[Optional[Sentence]]] = [
            [None] * self.number for _ in range(self.number)
        ]
        self.used_unique_classes: Set[type] = set()
        self.used_unique_ids: Set[Tuple] = set()
        self.generate_sentences()

    def clean(self):
        self.matrix = np.full((self.number, self.number), -1, dtype=int)
        self.generate_special_matrix()
        self.sentences = [[None] * self.number for _ in range(self.number)]
        self.used_unique_classes.clear()
        self.used_unique_ids.clear()
        self.generate_sentences()

    def generate_sentences(self) -> bool:
        for i in range(self.number):
            for j in range(self.number):
                if self.sentences[i][j] is None:
                    sentence_classes = self.all_sentence_classes.copy()
                    random.shuffle(sentence_classes)
                    for sentence_type in sentence_classes:
                        if sentence_type.UNIQUE and sentence_type in self.used_unique_classes:
                            continue
                        for params in self.backtrack_params(sentence_type.PARAM_TYPES, 0, []):
                            try:
                                sentence = sentence_type(*([(i, j)] + params))
                            except ValueError:
                                continue
                            if sentence_type.UNIQUE_ID and sentence.unique_id in self.used_unique_ids:
                                continue
                            if self.is_legal(sentence):
                                if sentence_type.UNIQUE:
                                    self.used_unique_classes.add(sentence_type)
                                if sentence_type.UNIQUE_ID:
                                    self.used_unique_ids.add(sentence.unique_id)
                                self.sentences[i][j] = sentence
                                if self.generate_sentences():
                                    return True
                                self.sentences[i][j] = None
                                if sentence_type.UNIQUE:
                                    self.used_unique_classes.remove(sentence_type)
                                if sentence_type.UNIQUE_ID:
                                    self.used_unique_ids.remove(sentence.unique_id)
                    return False
        return True

    def backtrack_params(self, param_types: List, index: int, path: List) -> Generator:
        if index == len(param_types):
            yield path
            return
        if isinstance(param_types[index], tuple):
            start, end = param_types[index]
            candidates = list(range(start, end))
            random.shuffle(candidates)
            for candidate in candidates:
                path.append(candidate)
                yield from self.backtrack_params(param_types, index + 1, path)
                path.pop()
        elif issubclass(param_types[index], Enum):
            candidates = list(param_types[index])
            random.shuffle(candidates)
            for candidate in candidates:
                path.append(candidate)
                yield from self.backtrack_params(param_types, index + 1, path)
                path.pop()

    def is_legal(self, sentence: Sentence) -> bool:
        return sentence.execute(self.matrix) == self.matrix[sentence.position[0], sentence.position[1]]

    def generate_special_matrix(self):
        matrix = np.zeros((self.number, self.number), dtype=int)
        option = random.choice([LineType.ROW, LineType.COLUMN, LineType.DIAGONAL])
        if option == LineType.ROW:
            row_idx = random.randint(0, self.number - 1)
            matrix[row_idx, :] = 1
        elif option == LineType.COLUMN:
            col_idx = random.randint(0, self.number - 1)
            matrix[:, col_idx] = 1
        elif option == LineType.DIAGONAL:
            if random.random() > 0.5:
                np.fill_diagonal(matrix, 1)
            else:
                for i in range(self.number):
                    matrix[i, self.number - 1 - i] = 1
        for i in range(self.number):
            for j in range(self.number):
                if random.random() > 0.5 and matrix[i, j] == 0:
                    temp_matrix = matrix.copy()
                    temp_matrix[i, j] = 1
                    rows_full = np.all(temp_matrix == 1, axis=1)
                    if np.sum(rows_full) > (1 if option == LineType.ROW else 0):
                        continue
                    cols_full = np.all(temp_matrix == 1, axis=0)
                    if np.sum(cols_full) > (1 if option == LineType.COLUMN else 0):
                        continue
                    if option != LineType.DIAGONAL:
                        main_diag_full = np.all(np.diag(temp_matrix) == 1)
                        anti_diag_full = np.all(np.diag(np.fliplr(temp_matrix)) == 1)
                        if main_diag_full or anti_diag_full:
                            continue
                    else:
                        main_diag_full = np.all(np.diag(temp_matrix) == 1)
                        anti_diag_full = np.all(np.diag(np.fliplr(temp_matrix)) == 1)
                        if main_diag_full and anti_diag_full:
                            continue
                    matrix[i, j] = 1
        self.matrix = matrix

    def check(self, matrix: NDArray[np.int_]) -> Tuple[bool, str]:
        if not self.check_line(matrix):
            return False, "您未能连成一线！"
        for i in range(self.number):
            for j in range(self.number):
                if self.sentences[i][j].execute(matrix) != matrix[i, j]:
                    return False, "您的逻辑有误！"
        return True, "您成功连成一线！"

    @staticmethod
    def check_line(matrix: NDArray[np.int_]) -> bool:
        if np.any(np.all(matrix == 1, axis=1)):
            return True
        if np.any(np.all(matrix == 1, axis=0)):
            return True
        if np.all(np.diag(matrix) == 1):
            return True
        if np.all(np.diag(np.fliplr(matrix)) == 1):
            return True
        return False
