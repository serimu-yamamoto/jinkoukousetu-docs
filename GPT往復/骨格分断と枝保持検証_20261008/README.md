# 第38巡 再現資料

[報告書](../GPT回答_多方向探索第38巡_枝を残す分断位置と開放骨格の製造条件_20261008.md)

calculate.pyはPython標準ライブラリのみ。inputs.jsonを読み、results.json、validation.json、beam_profiles.csv、fragment_ledger.csvを再生成する。plot.pyはmatplotlibとnumpyを使用する。実行環境：Python 3.12.14、matplotlib 3.11.2、numpy 2.5.3。

- [入力](inputs.json)／[計算](calculate.py)／[図生成](plot.py)
- [結果](results.json)／[45照合](validation.json)
- [枝の応力分布](beam_profiles.csv)／[480分断帳簿](fragment_ledger.csv)
- [モデル定義](model.md)／[一次資料](sources.md)
- [公開照合マニフェスト](publication-manifest.json)

物理試験0件、実物成功確率null。切断位置と確率は入力で、工程の達成値ではない。形態分類・計算照合の割合を雪感・安全の成功率にしない。
