# 第80巡の再現資料

[報告本文](../GPT回答_多方向探索第80巡_摩耗後も滑る接触部と混雑帯の耐久条件_20261009.md)を先に読む。全て計算・設計で、物理試験0件、成功確率未算定。

- [再計算コード](reproduce.py)、[入力](inputs.json)、[集約結果](summary.json)、[照合](verification.json)
- [モデルと適用範囲](model.md)、[一次資料](sources.json)、[採否](decision.json)
- [摩耗予算](wear_budget.csv)、[接点内集中](within_pad_wear.csv)、[要求比摩耗量](wear_requirements.csv)
- [相の露出割合](phase_exposure.csv)、[接触面積の効果](contact_localization.csv)、[全深度接触材費](full_depth_cap_inventory.csv)
- [膜模型の範囲](film_model_scope.csv)、[固定側と移動側の時間](body_role_contact_time.csv)
- [未実施試験](test_plan.json)、[Claude依頼](claude_handoff.md)
- [成果・索引監査](document_audit.json)、[監査コード](audit.py)、[索引差分履歴](index_changes.json)、[内容ハッシュ](manifest.json)

再実行：Python 3で `python reproduce.py --no-plots`。数値計算は標準ライブラリのみ。画像生成時は[requirements.txt](requirements.txt)のmatplotlibを追加してオプションなしで実行。画像は表示環境・ライブラリ版でバイトが変わり得る。CSV/JSONの数値と意味を照合する。自動実行で外部通信・公開・削除はしない。

53数式・収支照合、86比較行、2図。合格率・耐久保証へ換算しない。
