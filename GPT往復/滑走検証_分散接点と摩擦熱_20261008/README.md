# 第21巡の再現資料

[報告本文](../GPT回答_多方向探索第21巡_分散接点の摩擦熱と乾湿滑走の再設計_20261008.md)。物理試験0件、成功確率未算定。

- inputs.json：比較入力と出典・仮定の区別。
- calculate.py：標準ライブラリだけで計算。
- results.json：全条件と代表値・費用。
- validation.json：18項目の数値照合。物理実証ではない。
- plot.py：図の再生成（matplotlibを使用）。
- thermal_comparison.png／contact_layout.png：計算図・局部配置。
- sources.json：一次資料とアクセス範囲。本文のない資料から試験値を補わない。
- publication-manifest.json：公開時の成果パス・SHA256・バイト数。自己ファイルは一覧から除く。

再計算：このフォルダで python calculate.py、続いて python plot.py。作図はmatplotlib 3.11.2を用いた。JSONはUTF-8、非有限値を許可しない。公開本文・図・コードの照合後、作業用依存関係を含むローカル複製とGit履歴を削除する。

熱抵抗は円形の均一熱流束・半無限体の簡略比較。接点寸法、荷重、μ、E、比熱は実物未校正。図の面積平均と中心線ピークは別の量で、足し合わせない。費用は税抜の仮置き枠で、見積り・設備2億円の成立証明ではない。
