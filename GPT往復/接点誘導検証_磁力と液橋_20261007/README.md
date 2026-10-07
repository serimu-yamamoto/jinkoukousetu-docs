# 接点誘導の比較・再現資料（第9巡）

[報告本文](../GPT回答_多方向探索第9巡_磁力による接点誘導と液橋の比較_20261007.md)へ戻る。

物理試験0件。磁気双極子、既存クリップのすべり限界経路、接触球の液橋、仮の材料費を比較した。自然界での成功確率は算定していない。

| ファイル | 内容 |
|---|---|
| [inputs.json](inputs.json) | 全仮定、単位、M1/M1-Lの寸法と公差 |
| [reference_clip.json](reference_clip.json) | 第8巡の161点の力経路、参照コミットとSHA-256 |
| [calculate.py](calculate.py) | 標準ライブラリだけで計算・12整合性検証 |
| [results.json](results.json) | 300条件、公差128条件、液橋、材料費、全経路 |
| [plot.py](plot.py) | 計算結果から3図を作る原図コード |
| [force_comparison.png](force_comparison.png) | 経路の力、必要磁化、鋼平面、液橋 |
| [cost_comparison.png](cost_comparison.png) | 基準M1の仮費用と重量 |
| [functional_sequence.png](functional_sequence.png) | 部品機能と整地順序。製造図ではない |
| [sources.md](sources.md) | 一次資料と適用限界 |
| [探索台帳.md](探索台帳.md) | 比較した方向、反証、残す条件 |
| [検証記録.md](検証記録.md) | 再計算と文書照合 |

## 再計算

Python 3.10以降。リポジトリの同じ配置で実行する。

```text
python calculate.py
python plot.py
```

calculate.pyに追加ライブラリは不要。plot.pyはmatplotlibを用いる（今回の表示確認はPython 3.12・matplotlib 3.11.2）。元の第8巡JSONがあれば正規化SHA-256を照合し、不一致なら停止。フォルダ単独でもコピー済み経路で再計算できるが、元ファイル照合は未実施と結果に記録する。

出力中のJ_effは仮の有効磁化尺度で、実測Brや空隙磁束ではない。負の追加押込みは姿勢が既に合った理想経路上の意味であり、自由粒子の自動捕捉を意味しない。価格は全て未見積り。原著PDF・画像は収録せず出典へリンクした。

## 原データの由来

クリップ元ファイルはコミット9565960ab919415f20cdf2e29c73b8c0ff367c4aの第8巡results.json。refined_referenceのyとFを使い、u=(y_start−y)×50µm、F_N=F×0.000125Nで変換した。入口幅・E・厚さを変えた計算はこの経路の力を尺度変換し、元の無次元形状と摩擦係数0.2を保持する。別形状の再解法や面外安定性の計算ではない。
