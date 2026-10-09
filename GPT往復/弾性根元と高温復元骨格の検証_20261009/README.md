# 弾性根元と高温復元骨格の検証

第94巡。物理試験0件、成功確率未算定。具体グレードの根拠、24梁条件・12有限要素条件・27費用条件を保存。

- [報告](../GPT回答_多方向探索第94巡_高温復元骨格の候補と根元配置の成立条件_20261009.md)
- [出典](sources.md)／[模型](model.md)／[入力](inputs.json)
- [再計算](reproduce.py)／[結果](results.json)／[61照合](validation.json)
- [試験仕様](measurement_protocol.md)／[24未実施試片](test_plan.json)
- [Claude依頼](claude_handoff.md)／[研究状態](research_state.json)
- [図生成](draw.py)／[根元配置比較図](root_layout_comparison.png)
- [資料監査](audit.py)／[監査結果](document_audit.json)／[索引変更](index_changes.json)／[公開照合一覧](manifest.json)

[実行環境](environment.json)／[依存パッケージ](requirements.txt)。Python・NumPy・SciPyで `python reproduce.py --check`。図生成にはmatplotlibを使用。数値比較は相対許容1e-7で、物性同定や実物の性能検証ではない。
