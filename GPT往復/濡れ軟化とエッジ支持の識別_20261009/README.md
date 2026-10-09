# 第84巡：濡れ軟化とエッジ支持の識別

[主報告](../GPT回答_多方向探索第84巡_沈み込みと横抵抗から雪らしさを見分ける_20261009.md)。物理試験0件、成功確率未算定、設備・協力先未確保、照会・発注0件。

- [粒床試験案](bed_protocol.md)、[Claude依頼](claude_handoff.md)、[判断](decision.json)
- [一次資料3件](sources.json)、[比較仮定](inputs.json)、[模型と限界](model.md)
- [再計算コード](reproduce.py)、[集約](summary.json)、[20照合](checks.json)
- [245条件](parameter_sweep.json)、[6反例](paired_states.json)、[切削式の領域](dynamic_domain.json)
- [誤差上下限](measurement_bounds.json)、[未実施床割付](bed_plan.json)、[材料量と仮単価](material_quantities.json)
- [図のコード](draw.py)、[描画情報](plot_metadata.json)、[力だけでは分からない図](coupled_response.png)、[対応観測図](paired_observations.png)
- [文書監査](document_audit.json)、[監査コード](audit.py)、[履歴変更](index_changes.json)、[ファイル照合](manifest.json)

reproduce.pyはPython標準ライブラリのみ。draw.pyはmatplotlibとnumpy。291比較行と描画22,801節点は実験件数ではない。12床調製の24領域は未実施で、同じ床の対応領域を独立反復と数えない。仮費用は見積りではない。

原論文PDFは公開成果へ転載せず、URLと取得ハッシュを保存。図2点は自作の計算図で、目視確認済み。
