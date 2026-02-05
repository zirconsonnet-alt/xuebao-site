from __future__ import annotations

from typing import Dict, Iterable, Set

from ....domain.enums.core import Intervals
from ....domain.enums.harmony import Functions

def function_evidence(*, tonic_iv: Intervals, third_iv: Intervals) -> Dict[Functions, Dict[Intervals, float]]:
    """
    功能证据表：以当前 ChordInKeyAnalyzer 的实现为准（单一真源）。
    - 注意：Dominant 明确只认 M7（m7 完全不算）
    - Tonic 的 I/III 由调用方按“参照系统的 Base”传入（允许 Ionian/Major 与 Aeolian/Minor 自动切换 M3/m3）
    """
    return {
        Functions.Tonic: {tonic_iv: 1.0, third_iv: 3.0},
        Functions.Dominant: {Intervals.P5: 1.0, Intervals.M7: 3.0},
        Functions.Subdominant: {Intervals.P4: 3.0, Intervals.A4: 3.0, Intervals.m6: 2.0, Intervals.M6: 1.0},
    }


def score_functions_from_intervals(
    *,
    present: Iterable[Intervals],
    tonic_iv: Intervals,
    third_iv: Intervals,
) -> Dict[Functions, float]:
    """
    核心功能打分（与坐标系无关）：
    - 输入为“参照主音坐标系”下的 Intervals 集合
    - Dominant 的导音显式绑定为 Intervals.M7（m7 不算）
    """
    present_set: Set[Intervals] = set(present)
    result: Dict[Functions, float] = {f: 0.0 for f in Functions}

    evidence = function_evidence(tonic_iv=tonic_iv, third_iv=third_iv)

    for func, iv_weights in evidence.items():
        score = 0.0
        for iv, weight in iv_weights.items():
            if iv in present_set:
                score += weight
        result[func] += score
    return result


def score_function_tendencies(
    *,
    current_scores: Dict[Functions, float],
    flow: Dict[Functions, Dict[Functions, float]],
) -> Dict[Functions, float]:
    result: Dict[Functions, float] = {f: 0.0 for f in Functions}
    for src_func, dst_map in flow.items():
        src_score = current_scores.get(src_func, 0.0)
        if src_score == 0.0:
            continue
        for dst_func, ratio in dst_map.items():
            result[dst_func] += src_score * ratio
    return result
