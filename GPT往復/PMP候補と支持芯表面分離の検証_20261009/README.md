# 第92巡：PMP候補と支持芯／表面分離の検証

[報告書](../GPT回答_多方向探索第92巡_離型性と滑走性を分けたPMP複合枝の検証_20261009.md) / [Claudeへの依頼](claude_handoff.md)

- [一次資料](sources.json)、[研究状態](research_state.json)。
- [入力](inputs.json)、[模型](model.md)、[再計算](reproduce.py)、[結果](results.json)、[34算術照合](validation.json)。
- [未実施試験仕様](test_protocol.md)、[初期18組の割付](test_plan.json)。
- [図生成](draw.py)、[図の説明](plot_metadata.json)、[断面・界面の図](core_skin_sections.png)、[必要剛性・費用差額の図](stiffness_cost_frontiers.png)。
- [文書監査](audit.py)、[監査結果](document_audit.json)、[索引変更](index_changes.json)、[保存照合一覧](manifest.json)。

Python標準ライブラリで `python reproduce.py --check`。結果を生成する場合は `python reproduce.py`。図はmatplotlibで `python draw.py`。

15断面・60界面荷重条件・12摩擦予算・27費用差額を計算。算術照合は実験結果ではない。実証0件、成功確率未算定、材料未採用、設備・協力先未確保、照会・発注0件。50℃での複合剛性・接合・スキー摩擦・雪らしさは未測定。
