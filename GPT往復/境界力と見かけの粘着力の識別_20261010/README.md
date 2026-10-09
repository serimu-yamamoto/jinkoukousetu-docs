# 第118巡：境界力と見かけの粘着力の識別
[報告](../GPT回答_多方向探索第118巡_容器の支えを素材の粘着力と混同しない_20261010.md)／[Claude依頼](claude_handoff.md)。

- [入力](inputs.json)・[模型](model.md)
- [共通部品](../../計算部品/boundary_pressure.py)・[再現](reproduce.py)
- [結果](results.json)・[47件の数値確認](validation.json)
- [一次出典](sources.json)・[取得記録](source_acquisition.json)
- [未実施試験](test_plan.json)

python3 -B reproduce.py --check。実物試験0、成功確率null。既存の物性・試験を再現したシミュレーションではなく識別反例。
