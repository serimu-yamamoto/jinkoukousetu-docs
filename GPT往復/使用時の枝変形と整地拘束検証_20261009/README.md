# 第39巡 再現資料

[報告書](../GPT回答_多方向探索第39巡_分断後の枝支持と拘束を切り替える整地_20261009.md)

Python 3.12.14、numpy 2.5.3、scipy 1.18.1、matplotlib 3.11.2で実行。依存一覧は[requirements.txt](requirements.txt)。calculate.pyが同じフォルダのinputs.jsonを読み、結果・照合・CSVを生成する。plot.pyはその保存結果から図を生成する。ローカルの一時環境.work/.depsは公開照合後に削除する。

~~~text
python -m pip install -r requirements.txt
python calculate.py
python plot.py
~~~

- [入力](inputs.json)／[計算](calculate.py)／[図生成](plot.py)
- [全結果](results.json)／[35数値照合](validation.json)
- [96条件の枝](beam_cases.csv)／[参照枝の変形](beam_shapes.csv)／[27整地条件](grooming_residence.csv)
- [形と大変形の図](figure1_service_arm_profiles.png)／[滞在時間と相似の図](figure2_residence_and_scaling.png)
- [モデル定義](model.md)／[一次資料と適用範囲](sources.md)／[書誌JSON](sources.json)
- [公開マニフェスト](publication-manifest.json)

物理試験0件、実物成功確率null。型の製作、試験・購入・発注は行っていない。数値照合の35/35や条件数を、材料・スキー性能の成功率に使わない。
