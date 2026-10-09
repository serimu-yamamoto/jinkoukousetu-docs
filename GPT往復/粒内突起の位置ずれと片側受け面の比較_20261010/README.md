# 第124巡：粒内突起の位置ずれと片側受け面
[報告](../GPT回答_多方向探索第124巡_位置ずれに耐える粒内接点と付着の限界_20261010.md)／[Claude依頼](claude_handoff.md)。
[入力](inputs.json)、[模型](model.md)、[結果](results.json)、[59件の数値確認](validation.json)、[出典](sources.json)、[未実施仕様](test_plan.json)。
[共通部品](../../計算部品/stop_misalignment.py)／[再現](reproduce.py)。python3 -B reproduce.py --check。
実物0、成功確率null。面積は付着力ではない。短い突起の梁近似は三次元接触の保証ではない。
