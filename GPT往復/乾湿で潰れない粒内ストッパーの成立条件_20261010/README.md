# 第123巡：乾湿形状と粒内ストッパー
[報告](../GPT回答_多方向探索第123巡_乾燥形状の保持と粒内ストッパーの設計_20261010.md)／[独立検証依頼](claude_handoff.md)。
[入力](inputs.json)、[模型](model.md)、[結果](results.json)、[32数値確認](validation.json)、[出典](sources.json)、[未実施試験](test_plan.json)。
[共通部品](../../計算部品/drying_stop_geometry.py)と[再現](reproduce.py)。python3 -B reproduce.py --check。
実物0、成功確率null。再膨潤と乾燥形状保持を分ける。剛体突起の幾何計算は接着や滑走の保証ではない。
