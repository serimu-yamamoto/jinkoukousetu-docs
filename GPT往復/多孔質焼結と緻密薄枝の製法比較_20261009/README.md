# 第91巡：多孔質焼結と緻密薄枝の製法比較

[報告書](../GPT回答_多方向探索第91巡_内部孔に頼らない薄枝と製造費の両立_20261009.md) / [Claudeへの検証依頼](claude_handoff.md)

- [入力](inputs.json)、[計算](reproduce.py)、[結果](results.json)、[算術照合](validation.json)、[模型](model.md)。
- [一次資料記録](sources.json)、[研究状態](research_state.json)。
- [未実施試験仕様](test_protocol.md)、[24調製条件](test_plan.json)。
- [図の生成コード](draw.py)、[図の説明](plot_metadata.json)、[質量・雨の図](mass_stiffness_wet.png)、[構図・価格の図](manufacture_cost_boundary.png)。
- [文書監査](audit.py)、[監査結果](document_audit.json)、[索引変更履歴](index_changes.json)、[保存照合一覧](manifest.json)。

再計算：Python標準ライブラリだけで `python reproduce.py --check`。初回生成は `python reproduce.py`。画像はmatplotlibを別途利用して `python draw.py`。再計算は解析結果を照合する操作であり、物理試験ではない。

31断面・93水隙間条件・270価格条件、35算術照合。実験0件、成功確率未算定。50℃弾性率・密度の一部・全単価・良品率・荷重分担は仮定。薄枝が軽く量産しやすいと先に決めず、濡れ閉鎖と増量費を同時に比較する。資料や試片の作製・共有状況は[研究状態](research_state.json)で区別する。
