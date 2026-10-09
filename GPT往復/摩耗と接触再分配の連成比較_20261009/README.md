# 第81巡：摩耗と接触再分配

[研究報告](../GPT回答_多方向探索第81巡_摩耗で平らになる面と突き出す接点の比較_20261009.md)／[Claudeへの依頼](claude_handoff.md)。物理試験0件、成功確率未算定。

- [コード](reproduce.py)、[依存](requirements.txt)、[モデル](model.md)、[入力](inputs.json)
- [集約](summary.json)、[50数式・数値照合](checks.json)、[ソルバー診断](solver_diagnostics.json)、[出典](sources.json)
- [8経路の形状更新](evolution.csv)、[描画標本](profiles.csv)、[解析減衰との比較](analytic_decay_check.csv)、[刻み・格子比較](convergence.csv)
- [定常異相](stationary_phase_limits.csv)、[H81-P更新](recessed_support_evolution.csv)、[H81-P形状](recessed_support_profiles.csv)、[隙間限界](recess_clearance_limits.csv)
- [荷重変化](off_design_loads.csv)、[鋭い端部の非収束](sharp_edge_resolution.csv)
- [接触材在庫](cap_material_inventory.csv)、[表面加工量](finishing_inventory.csv)
- [設備未確保から始める初回18走行の依頼仕様案](first_test_request.md)（未送信・見積未取得）
- [未実施試験](test_plan.json)、[採否と進捗](decision.json)、[監査](document_audit.json)、[監査コード](audit.py)、[索引変更](index_changes.json)、[内容照合](manifest.json)

Pythonで依存を導入し `python reproduce.py`。生成先はこのフォルダ。計算で通信・公開・削除を行わない。50照合、146比較行、4,096描画標本、3図。検算と実証は別。環境情報は監査結果に含める。画像のバイトは描画版に依存し得る。
