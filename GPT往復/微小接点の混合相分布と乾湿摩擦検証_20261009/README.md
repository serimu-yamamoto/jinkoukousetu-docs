# 第67巡の再計算・試料仕様

[報告書](../GPT回答_多方向探索第67巡_低摩擦相を微小接点へ行き渡らせる材料設計_20261009.md)に結論、出典の限界、Claudeへの依頼を集約。物理試験0件、成功確率未算定。

- [入力](inputs.json)、[再計算コード](reproduce.py)、[導出](model.md)、[依存](requirements.txt)
- [結果・23数値照合](results.json)、[文書監査コード](audit.py)、[監査結果](audit_results.json)
- [140条件の接点分布](contact_presence.csv)、[偏在反例](cluster_counterexamples.csv)、[二種類の径](mixed_domain_sizes.csv)
- [加工費条件](conditional_process_cost.csv)、[歩留まり物量](manufacturing_yield.csv)
- [試料仕様](coupon_protocol.md)、[168行の未実施試験表](planned_coupon_tests.csv)
- [相分布図](phase_presence.png)、[偏在・費用図](clustering_and_cost.png)、[原典と取得状況](sources.json)

相へ触れる幾何割合を摩擦・荷重分担・雪感・実物成功率へ読み替えない。原料粉径を加工後相径へ移さない。CSVの未実施行の観測欄は空欄。
