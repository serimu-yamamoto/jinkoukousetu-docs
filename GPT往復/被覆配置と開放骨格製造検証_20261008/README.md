# 第34巡 再現資料

[報告書](../GPT回答_多方向探索第34巡_接触面の被覆配置と開放骨格の製造順序_20261008.md)。乾式被覆・部分膜・発泡前後・接触面の有限幅・製造費と摩耗の必要条件を比較する。物理試験0件、実物成功確率null。

|ファイル|内容|
|---|---|
|[inputs.json](inputs.json)|寸法、密度、被覆予算、仮単価・工程能力・損耗仮定|
|[calculate.py](calculate.py)|標準ライブラリだけで全計算を再現|
|[results.json](results.json)|全条件の計算値。確率・性能の学習モデルではない|
|[validation.json](validation.json)|29件の代数・単位に対応した数量・質量保存等の照合|
|[model.md](model.md)|式の定義、包絡密度／床密度、適用限界|
|[sources.md](sources.md)|一次資料7件、掲載値の差、確認範囲|
|[plot.py](plot.py)|2図の再生成|
|[図1](figure1_mass_and_expansion.png)|被覆量と発泡前後の被覆・厚さ|
|[図2](figure2_footprint_and_wear.png)|有限の接触幅と平均摩耗許容量|
|[publication-manifest.json](publication-manifest.json)|公開時の対象ファイル、バイト数とSHA256。自己ハッシュは含めない|

実行例（任意の作業環境へGitHubから取得した後）：

~~~text
python -X utf8 calculate.py
python -X utf8 plot.py
~~~

計算はPython 3.12.14で実行。図はmatplotlib 3.11.2（依存numpy 2.5.3）で作成し、2図を目視確認した。plot.pyはリポジトリ直下の一時.depsがあれば利用し、それ以外は通常のPython環境のmatplotlibを利用する。

掲載文献の9.12 wt%を再現したとはしない。同文献の掲載径・密度からは8.6363 wt%となった差を保存する。数値照合29件の通過は実物試験や成功確率ではない。成功判定には50℃、乾湿、雪感、人体・環境、冬の界面、雨後復旧、寿命、実費の同時確認が必要。

公開後は不可変コミットから全公開ファイルを再取得して照合し、依頼どおりローカル成果・一時資料・Git履歴を削除する。接続案内と既存利用設定は保護する。
