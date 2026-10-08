# 第36巡 再現資料

[報告書](../GPT回答_多方向探索第36巡_加圧で戻る材料と現地整地の分離_20261008.md)。加圧で低温成形できる材料を、現地整地と工場再生の両面から比較する。物理試験0件、実物成功確率null。

|ファイル|内容|
|---|---|
|[inputs.json](inputs.json)|一次論文4件の条件と、明示した設計仮定|
|[calculate.py](calculate.py)|標準ライブラリで再計算|
|[results.json](results.json)|加圧4条件、在庫6条件、購入費18条件、処理216条件、局部工具の処理速度36条件、MD単位監査|
|[validation.json](validation.json)|30件の単位・保存則・工程数量の照合|
|[model.md](model.md)|式・境界・適用限界|
|[sources.md](sources.md)|一次資料と元の実験条件、取得できなかった補足資料|
|[plot.py](plot.py)|2図の生成コード|
|[図1](figure1_pressure_and_time.png)|ローラーと閉じた加圧装置の力・保持時間|
|[図2](figure2_inventory_and_allowance.png)|相だけと粒全体の処理量・年間費用上限|
|[publication-manifest.json](publication-manifest.json)|公開対象のバイト数・SHA256。自己ハッシュは含まない|

~~~text
python -X utf8 calculate.py
python -X utf8 plot.py
~~~

Python 3.12.14で計算。図はmatplotlib 3.11.2（numpy 2.5.3）を使用し、一時.depsがあればそこから読み込む。2図を目視確認済み。加圧バッチを時間内に収められるという数値上の条件は、材料性能・型への充填・洗浄乾燥・検査までの実工程成立を示さない。

GitHubの不可変コミットから全対象を再取得し照合した後、ローカル成果・Git履歴・一時依存環境を削除する。接続案内と既存設定は保護する。
