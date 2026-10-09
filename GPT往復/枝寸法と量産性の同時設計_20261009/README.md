# 枝寸法と量産性の同時設計

[第86巡報告](../GPT回答_多方向探索第86巡_枝の柔らかさと雨後復帰を保つ寸法設計_20261009.md)の再現資料。物理試験0件・成功確率null。23数式等照合、267計算行、24未実施準備割付、2図。

- [入力](inputs.json)／[一次出典](sources.json)／[判断](decision.json)
- [式と範囲](model.md)／[計算](reproduce.py)／[要約](summary.json)／[数値照合](checks.json)
- [形状](geometries.json)／[力学](mechanical_screen.json)／[毛管閉鎖](wet_screen.json)／[断面感度](core_sensitivity.json)／[製造比較](production_comparison.json)
- [寸法比較の試験仕様](size_test_protocol.md)／[未実施割付](test_plan.json)／[Claudeへの依頼](claude_handoff.md)
- [乾湿の比較図](compliance_wet_tradeoff.png)／[寸法と加工量](geometry_production.png)／[図コード](draw.py)／[描画情報](plot_metadata.json)
- [文書監査](audit.py)／[監査結果](document_audit.json)／[索引更新の逆変換](index_changes.json)／[公開対象の照合一覧](manifest.json)

第三者のPDF・図は転載せず、URLと取得・照合範囲を記載。図は今回の計算から独自作成。計算はPython標準ライブラリ、描画はmatplotlib/numpy。
