# 粒の配向・直交輪・分流再生の再現資料

[第10巡の報告](../GPT回答_多方向探索第10巡_直交する開放輪と分流再生の設計条件_20261007.md)へ戻る。

物理試験0件、実物成功確率null。STLはmm単位の比較形状で、使用材料・量産方法・50℃性能が確定した製品ではない。

| ファイル | 内容 |
|---|---|
| [inputs.json](inputs.json) | 幾何・配向・振動・処理量・仮費用の入力 |
| [calculate.py](calculate.py) / [results.json](results.json) | 配向積分、独立MC照合、12数式検証、振動相似、処理量 |
| [build_geometry.py](build_geometry.py) / [mesh_validation.json](mesh_validation.json) | R0/R1生成、体積、平面支持姿勢 |
| [crossed_geometry.py](crossed_geometry.py) / [crossed_results.json](crossed_results.json) | R2一体化、連続経路、公差256条件、回転感度、体積上限による費用 |
| [plot.py](plot.py) | 経路・配向・分流工程の原図生成 |
| [validate_delivery.py](validate_delivery.py) | JSON、ソース、STLと相対リンクの保存前検証 |
| [requirements.txt](requirements.txt) | 今回の再現環境 |
| [sources.md](sources.md) | 一次資料と転用限界 |
| [探索台帳.md](探索台帳.md) / [検証記録.md](検証記録.md) | 試行の結果・範囲・未達事項 |

## 3D形状と原図

- [R0 平面](R0_planar.stl)
- [R1 波高30µm](R1_wave_30um.stl)
- [R1 波高60µm](R1_wave_60um.stl)
- [R2 線径50µm・開口60°](R2_crossed_wire50um.stl)
- [R2-L 線径44µm・開口64°](R2_crossed_wire44um.stl)
- [平面・波形の図](grain_geometry.png)
- [直交輪の図](crossed_geometry.png)
- [登録した二粒の連続経路](registered_path.png)
- [配向・時間・槽容量](orientation_and_process.png)
- [分流再生の工程案](selective_reconditioning.png)

R2のSTLはブーリアン和で背面を一体化したもの。R2-LはR1とは別案。2輪を固定メッシュ下地にする設計ではなく、各粒の形状である。逆経路があるため、数値形状の「リンク」と機械的な保持を区別する。

## 再計算の順番

Python 3.12で実行した。標準ライブラリ以外はrequirements.txtの4パッケージを使う。リポジトリのフォルダ配置を維持し、同じフォルダから順に実行する。

```text
python -m pip install -r requirements.txt
python calculate.py
python build_geometry.py
python crossed_geometry.py
python plot.py
python validate_delivery.py
```

calculate.pyの乱数種は1007。配向の主結果はGauss-Legendre積分で、MCは独立照合用。MCの標準誤差は数値積分の誤差尺度で、実物の成功率や信頼性ではない。

R2の連続経路は、本文第4章の解析条件が本体。メッシュの6姿勢照合や離散中心線はその補足であり、連続区間の証明の代わりにしない。公差計算は各粒の2輪の相対角を90°に固定し、二粒の本体姿勢を揃えている。自由姿勢、内部交差角の誤差、材料変形は未解決。

R2のかさ密度と費用は、仮粒数を固定して、接合部の重複を差し引かない体積上限から計算した。実測の充填性ではない。表の価格枠へ製造・取出し・仕上げ・検査を全て収める必要がある。

第三者論文・図の複製は収録せず、出典へリンクしている。
