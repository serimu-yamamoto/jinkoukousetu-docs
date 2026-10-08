# 第40巡の再現資料

[受け渡し報告](../GPT回答_多方向探索第40巡_50度クリープと経時変化を踏まえた枝の再設計_20261009.md)を入口にする。

- inputs.json: 出版社PDFのSHA256、図の校正座標、Table 6の平均値、費用仮定。
- reproduce.py: 図の色線抽出、表の平均値比、phr換算、年額と損益分岐の計算。
- creep_readings.csv / composition.csv / fiber_aging.csv / cost_sensitivity.csv: 再計算結果。欠測は補完しない。
- results.json: 18数値照合、数値結果、物理試験0・実物成功確率null。
- literature_comparison.png / conditioning_cost.png: 自作比較図。
- source_figure10c_crop.png: CC BY 4.0の原著図の切出し。権利・変更はATTRIBUTION.md。
- sources.json: 確認できた本文・方法と適用範囲。D1の元測定は未取得。
- environment.json / requirements.txt: 再計算時の環境。
- publication-manifest.json: 今回の変更ファイルのバイト数・SHA256。マニフェスト自身は含めない。

Python 3.12環境にrequirements.txtの依存を入れ、同じフォルダのreproduce.pyを実行する。RTK方針下では各コマンドをrtk summary経由にする。

~~~text
rtk summary python -m pip install -r requirements.txt
rtk summary python reproduce.py
~~~

図を再描画しない場合だけ --no-plots を追加できる。コードは隣接するリポジトリの .deps があれば優先するが、通常のPython環境でも動く。画像の読取り幅は実験の信頼区間ではない。物理実験やスキー性能検証を実施するコードではない。

元PDFの同一性確認はsources.json / inputs.jsonのSHA256を参照。PDF全体や、未取得のMendeley測定ファイルを保管済みとは主張しない。
