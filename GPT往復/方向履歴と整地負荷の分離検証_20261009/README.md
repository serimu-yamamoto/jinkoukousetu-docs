# 方向履歴と整地負荷の分離検証

第93巡。物理試験0件、成功確率未算定。方向変更の「量」だけでなく「間隔」を残す診断と、整地中／その後の滑走中の損耗を分ける比較案。

- [報告](../GPT回答_多方向探索第93巡_方向変更間隔を含む滑走面と整地の再設計_20261009.md)
- [一次資料・履歴](sources.md)／[模型](model.md)／[入力](inputs.json)
- [計算](reproduce.py)／[結果](results.json)／[算術照合](validation.json)
- [試験仕様](measurement_protocol.md)／[未実施割付](test_plan.json)
- [Claude依頼](claude_handoff.md)／[研究状態](research_state.json)
- [図生成](draw.py)／[活動度の図](history_activity.png)
- [資料監査](audit.py)／[監査結果](document_audit.json)／[索引変更](index_changes.json)／[公開照合用一覧](manifest.json)

再計算はPython標準ライブラリのみ：`python reproduce.py --check`。図はmatplotlibが必要。算術照合25件は物理試験件数ではない。
