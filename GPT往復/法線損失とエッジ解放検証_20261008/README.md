# H32 再現資料：法線損失とエッジ解放

物理試験0件。実物の成功確率はnull（未算定）。計算チェックの合格数から成功率を作らない。

- [入力](inputs.json)：論文の算術例と、出典で同定していない仮想係数を分離。
- [計算](calculate.py)：標準ライブラリのみ。
- [全結果](results.json)：48法線条件、9せん断条件、12反復条件、独立積分器との照合。
- [検証記録](validation.json)：23項目の数値・保存則確認。
- [導出と限界](model.md)、[一次資料](sources.md)。
- [図の再生成](plot.py)：matplotlib 3.11.2で作成。
- [図1](figure1_normal_loss_and_sinkage.png)、[図2](figure2_release_and_repetition.png)：独自モデルの図。第三者の図は転載していない。
- [公開照合一覧](publication-manifest.json)：掲載対象のバイト数とSHA256。manifest自身は自己参照ハッシュに含めず、公開時に別途照合。

~~~text
python -X utf8 calculate.py
python -X utf8 plot.py
~~~

同じディレクトリで実行するか、各スクリプトの完全なパスを指定する。出力はスクリプトと同じ場所。plot.pyはこのリポジトリの一時依存先.depsがあれば先に検索し、なければ通常のPython環境のmatplotlibを使用する。Python 3.12.14・matplotlib 3.11.2で動作を確認。図は環境のフォント等によってPNGバイトが変わり得る。物理係数の入力を変えた場合は結果・報告表・照合一覧を更新する。

本巡では一時作業フォルダーを使用し、GitHubの確定コミットから全対象を読み戻して照合後、研究ファイル・依存ライブラリ・論文一時ファイル・Git履歴を削除する。PCには接続案内と既存の設定だけを残す。
