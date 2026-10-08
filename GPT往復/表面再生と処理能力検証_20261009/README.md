# 第55巡の計算・図・検証一式

[報告書](../GPT回答_多方向探索第55巡_摩耗面の再生と材料交換を両立する設計_20261009.md)／[出典](sources.md)／[モデル](model.md)

物理試験0件、実物成功確率未算定。計算照合は物理実証ではない。

- inputs.json：前提・仮単価・仮の選別性能。
- calculate.py：Python 3標準ライブラリのみ。実行でresults.json、capacity.csv、classification.csv、renewal_cost.csv、validation.jsonを更新。
- draw.py：matplotlibが必要。3図のPNG/SVGを生成。未導入なら通常のPython環境へmatplotlibを用意する。
- test_plan.json：未実施の試験仕様。
- audit.py：文書・リンク・数値の確認。公開時の旧索引との照合には削除済みの作業用スナップショットを使用し、その結果を保存。
- document-audit.json：リンク・継承・数値・限界表示の確認。
- publication-manifest.json：自身を除く今回公開ファイルのバイト数とSHA-256。公開後に全ファイルをコミット固定URLから再取得して照合する。

実行例：このフォルダで python calculate.py。図の再作成は python draw.py。公開図は計算から作った図で、論文図や実験写真ではない。

経路を一つに固定せず、光による硬化、熱での型転写、接触層の更新、界面形成を比較する。現地60分の整地は工場での化学再生時間と別管理。
