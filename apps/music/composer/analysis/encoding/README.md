# analysis/encoding

编码向量仅包含**元信息**与**上下文信息（hit）**，不包含 evidence。

## Key 向量

由 `KeyVectorizer = KeyMetaVectorizer + KeyIndexVectorizer` 拼接而成。

### 1) KeyMetaVectorizer
- 维度：`12`
- 组成：
  - `base semitone profile`：12 维（主调式 base profile 的相对 semitone 集合）

### 2) KeyIndexVectorizer
- 维度：`7 + 12 = 19`
- 组成：
  - `main_mode_type`：7 维（Ionian..Locrian）
  - `tonic_pitch_class`：12 维（绝对主音 offset）

### 合计
- `KeyVectorizer.dim = 12 + 19 = 31`

---

## Mode 向量

由 `ModeVectorizer = ModeMetaVectorizer` 单独组成。

### ModeMetaVectorizer
- 维度：`12 + 7 = 19`
- 组成：
  - `base semitone profile`：12 维（mode base profile 的相对 semitone 集合）
  - `mode_type`：7 维（Ionian..Locrian）

---

## Chord 向量

由 `ChordMetaVectorizer` 单独组成。

### ChordMetaVectorizer
- 维度：`12`
- 组成：
  - `interval-class semitones`：12 维（相对根音的 semitone 集合）

---

## 上下文（hit）向量

### ChordInModeVectorizer
- 维度：`3 + 7 + 7 = 17`
- 组成：
  - `variant`：3 维（Base / Asc / Desc）
  - `degree`：7 维（I..VII）
  - `composition`：7 维（I..VII）

### ModeInKeyVectorizer
- 维度：`3 + 7 + 7 = 17`
- 组成：
  - `access flags`：3 维（Substitute / Relative / SubV）
  - `role modes`：7 维（Substitute 时的 mode）
  - `role degrees`：7 维（Relative/SubV 时的 degree）

