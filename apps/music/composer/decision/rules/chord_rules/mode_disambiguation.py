# Rule to reduce mode ambiguity under diatonic rotations.
from ..constraints import Constraint, Violation
from .utils import chord_info_from_candidate, resolve_key
from ....domain.enums.core import Degrees
from ....domain.enums.harmony import ModeAccess, VariantForm


class RelativeBaseModeDisambiguationRule(Constraint):
    """
    目的：减少“同一 diatonic 音集旋转”导致的三元组歧义。

    背景：在固定 key 下，主调式的 Base 音阶与其各级关系调（Relative）的 Base 音阶音集相同，
    这会让一个简单和弦（例如 Dm）既可以解释为：
    - Key=C Ionian, Mode=I (主调式), Chord=II
    - Key=C Ionian, Mode=II (D Dorian), Chord=I
    进而出现多个语义等价的三元组候选。

    规则：当选择“非 I 级关系调（Relative, role != I）”且和弦使用 Base 变体时，
    必须在该 mode 的坐标系里包含该 mode 的 characteristic_degree（调式特征音）。

    直觉：如果和弦本身不体现该调式的特征音，那么把它解释成“换到了该关系调”往往只是旋转重标，
    并不会带来新的色彩信息；此时倾向回落到主调式解释可以消除歧义，同时避免强制使用 Asc/Desc 引入离调音。
    """

    def check(self, ctx, candidate):
        key = resolve_key(ctx)
        if key is None:
            return None

        info = chord_info_from_candidate(ctx, candidate)
        if info is None:
            return None

        _, mode_id, chord_id = info

        if mode_id.access != ModeAccess.Relative:
            return None
        if not isinstance(mode_id.role, Degrees) or mode_id.role == Degrees.I:
            return None
        if chord_id.variant != VariantForm.Base:
            return None
        if chord_id.composition is None:
            return None

        mode = mode_id.resolve(key)
        chord_degrees_in_mode = {chord_id.degree + d for d in chord_id.composition}
        if mode.characteristic_degree in chord_degrees_in_mode:
            return None

        return Violation(code="mode_disambiguation", message="关系调(Base)需体现调式特征音以避免歧义")

