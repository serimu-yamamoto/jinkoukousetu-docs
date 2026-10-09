# 第110巡の再計算

24収支・算術照合、実証0件、成功確率null。

- [報告](../GPT回答_多方向探索第110巡_結晶接触材の粒度と保持量から製造を見直す_20261010.md)
- [模型](model.md)
- [共通部品](../../計算部品/powder_inventory.py)
- [コード](reproduce.py)
- [結果](results.json)
- [数値照合](validation.json)
- [資料](sources.json)
- [未実施比較](test_plan.json)
- [Claude依頼](claude_handoff.md)

サーバーで取得し、python3 -B reproduce.py --checkを実行。未生成なら--checkなしで生成する。Python標準ライブラリのみ。24確認は物理成功率ではない。
