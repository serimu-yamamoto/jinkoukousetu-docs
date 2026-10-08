# 第56巡の再計算・検証

[報告書](../GPT回答_多方向探索第56巡_接点が縮んで抜ける粒と雪の支えの両立_20261009.md)／[出典](sources.md)／[式と適用境界](model.md)

物理試験0件、実物成功確率未算定。

- inputs.json：仮形状・公差・摩擦感度・価格。
- calculate.py：Python 3標準ライブラリのみ。results.jsonと6つのCSV、validation.jsonを更新。
- draw.py：matplotlibで3図のPNG/SVGを再生成。
- test_plan.json：未実施の試験条件。
- audit.py／document-audit.json：文書・リンク・数値・公開時の旧索引保持の確認。
- publication-manifest.json：今回の全公開物の長さ・SHA-256（自身を除く）。

このフォルダで python calculate.py。図は python draw.py。公開時の監査は python audit.py。旧索引との比較用スナップショットはローカル清掃時に削除するが、監査結果と公開差分はGitHubへ残る。

公開原データの所在は確認したが、403のため未取得・未再解析。画像は自作モデルの図であり論文図の転載ではない。
