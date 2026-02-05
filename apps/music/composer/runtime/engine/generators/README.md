# engine/generators

Package for engine/generators

## 约束
- Key/Mode/Chord 的主生成路径必须使用“分层前缀展开（A->B->C...）+ 懒生成 + 懒洗牌”的枚举器。
- 每层候选集合只在进入该前缀分支时计算；该层遍历顺序必须是可复现的随机顺序（seed 固定则序列固定）。
- 任意分支下层候选为空时：仅跳过该分支并回溯，禁止整体早停。
- `limit` 表示最多产出多少个完整 id（tuple 或 id 对象）；空间耗尽则自然结束。
- `generator.py` 中的 SamplePlan/CandidateGenerator 仅作为备用采样工具，不作为 relations 的主生成逻辑。

## Contents
- __init__.py
- arrangement_generator.py
- chord_generator.py (ChordGenerator + ChordSpace)
- key_generator.py
- form_generator.py
- mode_generator.py (ModeGenerator + ModeSpace)
- generator.py
- enumeration.py

