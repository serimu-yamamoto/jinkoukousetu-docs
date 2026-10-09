# 第83巡：試験材グレードと交換試片の調達仕様

[主報告](../GPT回答_多方向探索第83巡_具体グレードと試片費用から絞る材料構成_20261009.md)。物理試験0件、成功確率未算定。設備・協力先未確保、照会・発注・見積取得0件。

- [材料・加工・数量仕様](procurement_spec.md)、[Claudeへの依頼](claude_handoff.md)
- [一次資料8件](sources.json)、[グレード別確認と欠測](materials.json)、[入力](inputs.json)
- [模型と限界](model.md)、[再計算コード](reproduce.py)、[集約](summary.json)
- [未実施24組の対応](trial_bindings.json)、[数量と仕上がり質量](bom.json)、[切り出し座標](cutting_layout.json)
- [材質置換の診断](material_scale.json)、[部分費用](cost_scenarios.json)、[12照合](checks.json)
- [判断記録](decision.json)、[文書監査](document_audit.json)、[監査コード](audit.py)、[索引変更](index_changes.json)、[ファイル照合](manifest.json)

Python 3でreproduce.pyを実行。標準ライブラリだけを使い、前巡の割付を読み込む。12算術・数量等の照合、14計算行、13配置矩形、24未実施割付。実測値・成功確率は生成しない。

原PDFや商品ページ本文は転載せず出典と取得PDFのハッシュを保存。試片寸法は施設合意前の案。PEEK小売価格と試験基本項目分を足した小計は、実見積り・完成試験費・コース材料費ではない。
