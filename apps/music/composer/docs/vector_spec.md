# 向量规格表（analysis 向量化接口）

本文档定义生成器使用的向量规范。所有向量按“拼接顺序”组织，顺序不可更改。

## 1. Chord 向量（vectorize_chord）

### 1.1 拼接顺序
1) Chord Meta
2) ChordInMode Index（仅当提供 mode 时）
3) （已移除）Chord Evidence
4) （已移除）ChordInMode Evidence（仅当提供 mode 且命中 hit 时）

> 没有 mode 时，不追加 2)。

### 1.2 Chord Meta（19 维）
- [ChordMeta.scale_pitch_class] 12 维
  - 含义：base 音阶的 pitch class 集合（0..11 多热）
  - 顺序：0,1,2,3,4,5,6,7,8,9,10,11
- [ChordMeta.composition_degrees] 7 维
  - 含义：和弦组成音级（Degrees.I..VII 多热）
  - 顺序：I, II, III, IV, V, VI, VII

### 1.3 ChordInMode Index（17 维）
- [ChordInModeIndex.variant] 3 维
  - 含义：VariantForm 多热
  - 顺序：Base, Ascending, Descending
- [ChordInModeIndex.degree] 7 维
  - 含义：和弦根音在调式中的音级（Degrees.I..VII 多热）
  - 顺序：I, II, III, IV, V, VI, VII
- [ChordInModeIndex.composition] 7 维
  - 含义：和弦音级映射到调式后的集合（Degrees.I..VII 多热）
  - 顺序：I, II, III, IV, V, VI, VII

### 1.4 Chord Evidence（已移除）
说明：Chord 纯实体 evidence 已删除；此类“和弦本体特征”应由 domain 层（Chord/Quality）提供。

### 1.5 ChordInMode Evidence（已移除）
说明：ChordInMode 的派生特征已迁入 hit（`analysis/core/hits/chord_in_mode.py`），不再作为独立向量拼接段。


## 2. Mode 向量（vectorize_mode）

### 2.1 拼接顺序
1) Mode Meta
2) ModeInKey（Access + 派生特征已在 hit 内计算，仅当提供 key 且命中 hit 时）

> 没有 key 时，不追加 2)。

### 2.2 Mode Meta（21 维）
- [ModeMeta.tonality] 2 维
  - 含义：Tonality 多热
  - 顺序：maj, min
- [ModeMeta.base_pitch_class] 12 维
  - 含义：mode base 变体音阶的 pitch class 集合（0..11 多热）
  - 顺序：0,1,2,3,4,5,6,7,8,9,10,11
- [ModeMeta.mode_type] 7 维
  - 含义：Modes 枚举独热
  - 顺序：Ionian, Dorian, Phrygian, Lydian, Mixolydian, Aeolian, Locrian

### 2.3 ModeInKey Evidence（已移除）
说明：ModeInKey 的派生特征已迁入 hit（`analysis/core/hits/mode_in_key.py`）。

### 2.4 ModeInKey Access（17 维）
- [ModeInKeyAccess.access_type] 3 维
  - 含义：访问方式（Key.__getitem__ 的来源）
  - 顺序：Substitute, Relative, SubV
- [ModeInKeyAccess.mode_role] 7 维
  - 含义：当 access=type 时，角色为 Modes 枚举独热
  - 顺序：Ionian, Dorian, Phrygian, Lydian, Mixolydian, Aeolian, Locrian
- [ModeInKeyAccess.degree_role] 7 维
  - 含义：当 access=Natural/SubV 时，角色为 Degrees 独热
  - 顺序：I, II, III, IV, V, VI, VII


## 3. Key 向量（vectorize_key）

### 3.1 拼接顺序
1) Key Meta
2) Key Index

### 3.2 Key Meta（14 维）
- [KeyMeta.base_pitch_class] 12 维
  - 含义：key 主调式 base 变体音阶的 pitch class 集合（0..11 多热）
  - 顺序：0,1,2,3,4,5,6,7,8,9,10,11
- [KeyMeta.tonality] 2 维
  - 含义：主调式的 Tonality 多热
  - 顺序：maj, min

### 3.3 Key Index（19 维）
- [KeyIndex.main_mode_type] 7 维
  - 含义：主调式 Modes 枚举独热
  - 顺序：Ionian, Dorian, Phrygian, Lydian, Mixolydian, Aeolian, Locrian
- [KeyIndex.tonic_pitch_class] 12 维
  - 含义：key 主音 pitch class（0..11 多热）
  - 顺序：0,1,2,3,4,5,6,7,8,9,10,11


## 4. 向量维度总览
- Chord Meta: 19
- ChordInMode Index: 17
- Chord Evidence: （已移除）
- ChordInMode Evidence: （已移除）
- Mode Meta: 21
- ModeInKey Evidence: （已移除）
- ModeInKey Access: 17
- Key Meta: 14
- Key Index: 19


## 5. 注意事项
- “访问方式”信息归属于关系层（ChordInMode / ModeInKey），不在实体本体向量中重复。
- 缺省参数（未提供 mode/key）时不追加对应关系向量。
- 所有向量均为 float（0.0/1.0）。
