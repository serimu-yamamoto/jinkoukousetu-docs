# 第113巡：実測動的物性と高周波推定の識別

特定UHMWPEの1Hz・30/50℃データから支持補償と損失を分ける。53数値確認、本プロジェクトの実物試験0件、成功確率null。

- [報告](../GPT回答_多方向探索第113巡_50度の実測物性から支持と滑走損失を分ける_20261010.md)
- [実測値の転記](measured_inputs.json)
- [模型](model.md)
- [共通部品](../../計算部品/response_identifiability.py)
- [再利用したSLS部品](../../計算部品/viscoelastic_glide.py)
- [コード](reproduce.py)
- [結果](results.json)
- [数値確認](validation.json)
- [一次出典](sources.json)
- [未実施仕様](test_plan.json)
- [Claudeへの依頼](claude_handoff.md)

サーバー上のこのフォルダで `python3 -B reproduce.py --check`。Python標準ライブラリのみ。--checkなしで結果生成。一次資料のPDFは転載せず出典参照。1Hzの測定点へ一致することは、高周波での妥当性の証明ではない。
