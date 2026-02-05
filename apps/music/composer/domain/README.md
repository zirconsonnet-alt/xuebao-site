# domain 包文档（Core Music Domain）

> 目标：提供一套**不可变（immutable）**、**可驻留（interned）**、可组合的音乐领域对象（Key / Mode / Scale / Chord …），并用一组运算符表达“音乐计算”（索引、音程变换、集合关系、差分/转移等）。

---

## 设计总览

### 1) 不可变 + Intern（去重共享）
- **不可变**：多数核心对象继承 `FrozenSlotsMixin`，初始化结束调用 `_freeze()`，之后禁止 `__setattr__` 变更。
- **驻留（Intern）**：多数核心对象使用 `InternedMeta`，通过 `_cache_key(...)` 计算 key，并在 `WeakValueDictionary` 中缓存，达到：
  - 相同语义对象共享同一实例（减少内存/加速比较）
  - 值对象语义（hash/eq 稳定）

> 受影响对象：`BaseNote / Scale / Mode / Key / Chord / Quality / ColorShift / Transition`  
> 不驻留：`Form / Section`（目前是普通 dataclass）

---

## 对象职责一览

- **BaseNote**：音名（C D E F G A B）+ 升降号 shifts（-2..+2）→ pitch class（offset 0..11）
- **Intervals**（enum）：音程（degree + semitone），可 `+/-` 合成/相减
- **Scale**：主音 tonic + 7个 interval profile → 7个 BaseNote 序列
- **Mode**：调式类型（Ionian…Locrian）+ 主音 tonic，内含 variant → scale 的缓存
- **Key**：主音 tonic + 主调式 main_mode_type，构建：
  - `modes_by_type`: 同主音不同调式
  - `modes_by_degree`: 按主调式的 1~7 级导出的各级调式（degree_mode）
  - `ModeAccess.SubV`: 目前固定实现为“目标级音上方小二度为根的 Mixolydian”
- **Chord**：以某个 `Scale` 为“根音音阶”，`composition` 为**相对根音的级数集合**（必须含 I）
- **Quality**：和弦音程集合推断出的质量（base quality + tensions + omits）
- **ColorShift**：两个 Scale interval profile 之间的色彩迁移（含 pitch class diff）
- **Transition**：从 src quality 到 dst quality 的“功能迁移”+ 根音差（0..11）
- **Form/Section**：曲式结构（段落标签、长度、角色、引用信息等）

---

## 运算符矩阵（对象 × 运算符）

> 表格纵轴：对象  
> 表格横轴：运算符（“计算语义/返回类型”）

| 对象 \\ 运算符 | `str(x)` | `x == y` | `x + y` | `x - y` | `x \| y` | `x[key]` | `key in x` | `iter(x)` | `len(x)` |
|---|---|---|---|---|---|---|---|---|---------|
| **BaseNote** | `C#/Db` | note_name+shifts | `BaseNote + Intervals -> BaseNote` | `BaseNote - Intervals -> BaseNote` | `BaseNote \| BaseNote -> Intervals` | — | — | — | — |
| **Scale** | `C, D, E.../F, G, A...` | tonic+intervals | `Scale + ColorShift -> Scale` | `Scale - Scale -> ColorShift` | `Scale \| BaseNote -> Degrees?` | `Scale[Degrees] -> BaseNote` | `BaseNote in Scale` | 可迭代 7 音 | `7` |
| **Chord** | `Cmaj/Dmin` | scale+composition | `Chord + Transition+ColorShift -> Chord` | `Chord - Chord -> Transition+ColorShift` | `Chord \| BaseNote -> Degrees?` | `Chord[Degrees] -> BaseNote` | `BaseNote in Chord` | 可迭代 chord tones | 和弦音数量 |
| **Mode** | `C-Ionian/C-Dorian` | tonic+mode_type | — | — | `Mode \| Scale -> set[degree,variant]` | `Mode[deg,variant] -> Chord`；`Mode[deg,variant,comp] -> Chord` | `BaseNote in Mode` / `Scale in Mode` | — | — |
| **Key** | `Ionian调性/Aeolian调性` | tonic+main_mode_type | — | `Key - Key -> set[Degrees\|Modes]` | `Key \| Mode -> Modes\|Degrees?` | `Key[Modes] -> Mode`；`Key[Degrees] -> Mode`；`Key[deg,ModeAccess] -> Mode` | `Mode/Scale/BaseNote in Key` | — | — |
| **Quality** | `maj7/no5` | base+tensions+omits | — | — | — | — | — | — | —       |
| **ColorShift** | `ShiftA/ShiftB` | src+diff+dst | — | — | — | — | — | — | —       |
| **Transition** | `src-diff-dst/src-diff-dst` | src+diff+dst | — | — | — | — | — | — | —       |
| **Form** | `FormA/FormB` | dataclass+fields | — | — | — | — | — | — | —       |
| **Section** | `SectionA/SectionB` | dataclass+fields | — | — | — | — | — | — | —       |

---

## 关键语义说明（避免误用）

### A. “|” 运算符在不同对象上的统一意图：**反查/对齐（lookup/align）**
- `BaseNote | BaseNote -> Intervals`：从一个音到另一个音的音程
- `Scale | BaseNote -> Degrees?`：该音是否等于某级（严格等于 BaseNote 实例语义，不做 respell）
- `Chord | BaseNote -> Degrees?`：该音在 chord 中属于哪个 degree（并要求 degree 在 composition 内）
- `Mode | Scale -> set[degree,variant]`：该 scale 在此 mode 的哪些派生位置出现
- `Key | Mode -> Modes|Degrees?`：该 mode 在此 key 的按 type/degree 的索引

> 总结：`|` 基本都在做“给我一个对象，我告诉你它在我这里的位置/相对关系”。

### B. `Chord.composition` 的坐标系：**相对根音（Degrees.I 为根音）**
- `composition` 必须包含 `Degrees.I`
- `Chord.scale` 的 `tonic` 视为 chord root（因此 `Chord[Degrees.I]` 是根音）
- 由 `composition` 结合 `scale` 派生 `base_notes`
- 由 `composition` 推断根音到其它 chord tone 的 semitone → `Intervals.get((degree,semitone))` → `Quality.from_intervals(...)`

### C. `Mode.__getitem__` 的索引语义：**(degree, variant[, composition])**
- `(degree, variant)`：返回该 degree 派生 scale 上的默认 triad
- `(degree, variant, composition)`：返回指定 composition 的 chord  
这使得“Mode 访问 Chord”的接口天然携带“和弦来自 mode 的哪个 degree/variant”。

### D. `Key[(degree, ModeAccess.SubV)]` 当前实现是硬编码策略
- 取主调式 base scale 的 `degree` 音
- 上方小二度作为 sub_root
- 返回 `Mode(sub_root, Mixolydian)`
> 如果未来需要更一般的替代/属功能体系，建议把 SubV 规则抽象为可配置策略（Strategy/Registry），而不是固定写死在 Key 内。

---

## 索引（__getitem__）详细说明

本节专门说明核心对象的 `[]` 访问语义，避免把“查值”与“反查/对齐”混淆（反查请用 `|`）。

### 1) `BaseNote`
> **不提供 `[]` 访问**  
BaseNote 是原子对象，索引没有语义。

### 2) `Scale`
**语义：按级数取音**
- `Scale[Degrees] -> BaseNote`
- 例：`C大调` 的 `Scale[Degrees.I] == C`，`Scale[Degrees.V] == G`

**错误用法**
- 传入非 `Degrees` 会抛 `TypeError`/`KeyError`
- 想“问这个音属于哪一级”，请用 `Scale | BaseNote`

### 3) `Chord`
**语义：按 chord 内部级数取音**
- `Chord[Degrees] -> BaseNote`
- 注意：`Chord` 的 `Degrees` 是**相对根音**坐标（composition 的坐标系）
- 例：`Cmaj` 的 `Chord[Degrees.I] == C`，`Chord[Degrees.III] == E`

**相关运算**
- 想“某个音是否在 chord 内并属于哪一度”，请用 `Chord | BaseNote`

### 4) `Mode`
**语义：根据 degree/variant 生成派生 chord**
- `Mode[(degree, variant)] -> Chord`（默认三和弦）
- `Mode[(degree, variant, composition)] -> Chord`（指定 composition）

**说明**
- `degree` 表示“从当前 mode 出发的派生级数”
- `variant` 表示使用哪个 scale variant（Base/Ascending/Descending）
- `composition` 必须以 `Degrees.I` 为根音坐标

### 5) `Key`
**语义：在 key 内取 mode**
- `Key[Modes] -> Mode`（同主音不同调式）
- `Key[Degrees] -> Mode`（按主调式的级数导出的调式）
- `Key[(degree, ModeAccess)] -> Mode`
  - `ModeAccess.Relative`：等价于 `Key[degree]`
  - `ModeAccess.SubV`：使用 SubV 规则生成替代调式（目前是硬编码）

**错误用法**
- 想反查某个 mode 在 key 中的“角色”，请用 `Key | Mode`
