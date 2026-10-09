# 第79巡の計算・検証資料

[報告書](../GPT回答_多方向探索第79巡_可動部を省く弾性層と滑り抵抗の交換条件_20261009.md)／[Claudeへの受け渡し](claude_handoff.md)

物理試験0件、成功確率未算定。30数式・数値照合、479比較行、1,280描画用標本、2図、8未実施試験仕様。一次資料の閲覧範囲はsources.json。

Pythonとrequirements.txtの依存関係を用意してreproduce.pyを実行します。実行に元のClaudeコードは不要です。生成物はこのフォルダだけへ書き出します。

- inputs.json：設計仮定。E・ν・価格・寿命は完成品測定値ではありません。
- model.md：式、零モード、接触制約、線形性、横力、費用の範囲。
- pressure_profiles.csv：1,280点は図の標本で、独立の試験条件ではありません。
- summary.json／checks.json：数式・数値検証。物理的な性能保証ではありません。
- audit.py／document_audit.json：数値転記・リンク・履歴保護の確認。
- manifest.json：今回の公開成果のバイト数とSHA256。manifest自身は含めません。

## ファイル

- [area_shear_tradeoff.csv](area_shear_tradeoff.csv)
- [checks.json](checks.json)
- [claude_handoff.md](claude_handoff.md)
- [coating_throughput.csv](coating_throughput.csv)
- [concept.png](concept.png)
- [contact_results.csv](contact_results.csv)
- [coupling_diagnostic.csv](coupling_diagnostic.csv)
- [decision.json](decision.json)
- [frequency_requirements.csv](frequency_requirements.csv)
- [grid_convergence.csv](grid_convergence.csv)
- [inputs.json](inputs.json)
- [layer_tradeoffs.png](layer_tradeoffs.png)
- [material_cost.csv](material_cost.csv)
- [mode_response.csv](mode_response.csv)
- [model.md](model.md)
- [pressure_profiles.csv](pressure_profiles.csv)
- [reproduce.py](reproduce.py)
- [requirements.txt](requirements.txt)
- [scale_separation.csv](scale_separation.csv)
- [skin_stiffening.csv](skin_stiffening.csv)
- [sources.json](sources.json)
- [summary.json](summary.json)
- [test_plan.json](test_plan.json)
