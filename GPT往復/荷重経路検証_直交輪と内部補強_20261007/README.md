# 第11巡 再現資料

[本文](../GPT回答_多方向探索第11巡_閉じた補強輪による支持と局所変形の分離_20261007.md)を先に読む。対象は未校正の形状・小変形計算であり、50℃での実物試験は行っていない。

## ファイル

- [共通入力](inputs.json)、[曲線骨組と直線補強の計算](calculate.py)、[直線補強の全結果](results.json)
- [閉円補強の計算](closed_hoop.py)、[閉円補強の全結果](hoop_results.json)
- [形状生成](geometry.py)、[形状検査](geometry_validation.json)
- R4-120：[STL](R4_open120_wire44um.stl) / [SCAD](R4_open120.scad)
- R4-150：[STL](R4_open150_wire44um.stl) / [SCAD](R4_open150.scad)
- [描画](plot.py)、[設計比較](design_comparison.png)、[荷重と費用](mechanics_and_cost.png)、[立体図](R4_solid_shapes.png)
- [検証コード](validate_delivery.py)、[検証結果](validation.json)、[検証記録](検証記録.md)
- [出典](sources.md)、[探索台帳](探索台帳.md)、[依存関係](requirements.txt)

## 再実行

Pythonへrequirements.txtのパッケージを導入し、calculate.py、closed_hoop.py、geometry.py、plot.py、validate_delivery.pyの順に実行する。共通入力・計算・出力は同じフォルダへ置く。リポジトリ直下に.depsがある場合はその一時パッケージを優先する。描画キャッシュは直下.scratchへ入る。

図の線画は中心線の説明、STL/SCADはmm単位の形状候補。線形骨組の交点剛接は一体STLの応力を再現した保証ではない。各数値結果のphysical_testsは0、success_probabilityはnull。

入力のE=300MPa、ν=0.45、κ=0.85、粒数、材料密度、500円/kg、年補充2%は仮定。線形診断値は安全許容値ではない。幾何の通過条件数・数式一致を成功率へ換算しない。環境への2%放出を認める費用模型でもない。
