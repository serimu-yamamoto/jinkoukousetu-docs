# 多孔質薄片の一括製造と面仕上げ

[第85巡報告](../GPT回答_多方向探索第85巡_油を使わない多孔質薄片の製造と量産条件_20261009.md)の再現資料。製造・物理試験0件、成功確率null。21数式等照合、117計算行、24未実施割付、2図。

- [出典](sources.json)／[入力](inputs.json)／[判断](decision.json)
- [模型](model.md)／[計算](reproduce.py)／[結果要約](summary.json)／[数値照合](checks.json)
- [初案形状](geometry.json)／[敷き詰め形状](nested_geometry.json)／[面の緻密化](skin_sweep.json)／[粉末寸法](powder_scale.json)
- [初案在庫](inventory.json)／[初案ライン](line_requirements.json)／[初案部分費](material_heat_costs.json)
- [改良案収支](route_comparison.json)／[切断換算](cutting_requirements.json)／[文献換算](literature_conversion.json)
- [製造・診断仕様](manufacturing_protocol.md)／[未実施24割付](manufacturing_test_plan.json)／[Claudeへの依頼](claude_handoff.md)
- [構造図](manufacturing_concept.png)／[歩留まり・部分費図](yield_cost_tradeoff.png)／[図コード](draw.py)／[描画情報](plot_metadata.json)
- [文書監査コード](audit.py)／[監査結果](document_audit.json)／[索引更新の逆変換](index_changes.json)／[公開照合用一覧](manifest.json)

計算はPython標準ライブラリ。図はmatplotlib/numpy。文献PDFや著者図は転載せず、一次資料へのURL・照合値を保存した。
