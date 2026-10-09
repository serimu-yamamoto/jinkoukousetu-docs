# 第82巡：初回実証の設備照合と試験費用

[主報告](../GPT回答_多方向探索第82巡_設備未確保から始める実証と試験費用_20261009.md)。物理試験0件、成功確率未算定、協力先未確保、照会未送信。

- [改訂試験仕様](protocol.md)、[照会文案](inquiry_draft.md)、[Claude依頼](claude_handoff.md)
- [一次情報9件](sources.json)、[条件](inputs.json)、[計算の説明](model.md)、[再計算コード](reproduce.py)
- [集約](summary.json)、[25算式・単位・割付照合](checks.json)、[18走行の未実施割付](main_run_plan.json)
- [回転と接触履歴](geometry.json)、[摩耗の検出量](wear_detection.json)、[力の不確かさ](force_uncertainty.json)
- [基本料金の算術例](cost_scenarios.json)、[作業時間の感度](time_scenarios.json)、[設備選定記録](decision.json)
- [文書監査](document_audit.json)、[監査コード](audit.py)、[索引変更](index_changes.json)、[ファイル照合](manifest.json)

再計算はPython 3で python reproduce.py。追加ライブラリ不要、出力は同じフォルダ。23計算行に別途18本の未実施割付を収録。実データを模した行や実証合格率は生成しない。公開料金と仮作業時間は実見積りではない。
