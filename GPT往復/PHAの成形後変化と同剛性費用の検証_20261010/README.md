# 第97巡 再計算入口

[報告](../GPT回答_多方向探索第97巡_PHAの結晶性と成形後硬化から見直す材料設計_20261010.md)／[出典](sources.md)／[模型](model.md)／[Claude依頼](claude_handoff.md)／[未実施試験](test_plan.md)。

物理試験0件、成功確率未算定。PHAは比較候補であり、採用材料ではない。

- inputs.json：文献の時間指数・密度と、費用・E50の仮入力を分けた。
- reproduce.py / results.json：剛性変化12条件、保持時間36条件、同剛性費用24条件、価格境界と工程在庫。Python標準ライブラリだけで実行できる。
- validation.json：逆算・単位・物量の85照合。材料試験数ではない。
- make_figure.py / aging_and_price_bounds.png：計算比較の1図。matplotlibを使う。
- test_plan.json：36組72片。測定欄は全て未実施。
- research_state.json：物理証拠と協力先の未確定状態。
- audit.py / document_audit.json：文書・値・リンク・履歴を確認。
- index_changes.json / manifest.json：索引履歴の保存と公開ファイル照合。

このフォルダでの実行例：

```text
rtk summary python reproduce.py --check
rtk summary python make_figure.py
rtk summary python audit.py
```

--checkなしのreproduce.pyは結果を書き、--checkは再計算して保存バイトを照合する。仮定の全条件を通っても成功確率には換算しない。第三者の論文・図・PDF・依存ライブラリは同梱しない。
