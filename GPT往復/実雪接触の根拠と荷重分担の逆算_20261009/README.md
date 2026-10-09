# 実雪接触の根拠と荷重分担の逆算（第87巡）

[報告](../GPT回答_多方向探索第87巡_実雪の接触根拠と高さ分布から見直す荷重設計_20261009.md) → [模型](model.md) → [未実施計測仕様](measurement_protocol.md) → [Claudeへの反証依頼](claude_handoff.md)。

- 入力：[inputs.json](inputs.json)、[一次資料](sources.json)、[速度範囲の監査](reference_scope.json)。
- 再現：Python標準ライブラリで `python reproduce.py`。23照合・177計算レコード。[照合結果](checks.json)、[集計](summary.json)。
- 計算：[接点参加](contact_recruitment.json)、[独立積分](quadrature_check.json)、[識別不能の対](nonidentifiability.json)、[逆算窓](inverse_windows.json)、[設計例と高荷重反例](design_witness.json)。
- 図：[接触分担](contact_recruitment.png)、[隙間の設計](design_window.png)。`python draw.py`で再作図（matplotlib/numpy）。図は自作、第三者図の転載なし。
- 未実施：[観測計画](test_plan.json)、[判断記録](decision.json)。
- 保存照合：[履歴追記](index_changes.json)、[文書監査](document_audit.json)、[公開対象SHA256](manifest.json)。

物理試験0件。設備・協力先未確保。成功確率未算定。仮の物性・高さ・固定基点による解析であり、滑走・人体安全・雨後復旧は未実証。23照合は実験数ではない。
