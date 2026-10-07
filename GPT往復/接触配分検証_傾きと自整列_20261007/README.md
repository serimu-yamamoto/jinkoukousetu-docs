# 第12巡 再現資料

[報告本文](../GPT回答_多方向探索第12巡_接触の偏りと自整列の成立条件_20261007.md)を先に読む。単粒・仮定材料・指定支持での数値計算であり、実物や粒群床の検証ではない。

## 内容

- [共通入力](inputs.json)、[曲線骨組の線形応答](elastic_core.py)
- [接触平衡](contact_model.py)、[全488条件](contact_results.json)
- [姿勢と重心](gravity.py)、[重心・斜面・力尺度の結果](gravity_results.json)
- [診断境界と内部点収束](thresholds.py)、[境界の結果](threshold_results.json)
- [描画](plot.py)、[接触の図](contact_sensitivity.png)、[姿勢の図](gravity_orientation.png)、[斜面の図](slope_support.png)
- [数値検証](validate_delivery.py)、[検証結果](validation.json)、[検証記録](検証記録.md)
- [出典](sources.md)、[探索台帳](探索台帳.md)、[依存関係](requirements.txt)

## 再実行

Pythonにrequirements.txtのライブラリを導入し、contact_model.py、gravity.py、thresholds.py、plot.py、validate_delivery.pyの順に実行する。計算はこのフォルダに結果を保存する。リポジトリ直下の.depsが存在する場合は一時ライブラリとして優先する。描画キャッシュは直下.scratchへ入る。

第11巡フォルダのhoop_results.jsonおよび2つのSTLを相対パスで参照するため、リポジトリのフォルダ構成を保つ。参照元は[第11巡](../荷重経路検証_直交輪と内部補強_20261007/README.md)、作成時の基準commit f44df333080a93c174df462ef36c02890bb289f2。巨大な形状ファイルの複製は作らない。

単位はN、mm、MPa。図の荷重はmN、長さはµmへ換算。E=300MPaなどは仮定。1%などの診断値は材料許容値ではない。physical_tests=0、success_probability=nullを維持する。

Hertz接触は丸端と局所半無限弾性体の近似。自由回転支持は理想境界で、実床に回転継手があるという意味ではない。重心最小は静的な条件付き解析で、整列率・整列時間は出力しない。後端拘束・単粒・小変形の範囲を超える値を採用根拠にしない。
