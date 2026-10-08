# 第18巡 再現資料

[報告本文](../GPT回答_多方向探索第18巡_濡れ乾きに耐える枝支持と粒内接合_20261008.md)の再現用。実物試験0件、実物成功確率null。モデルは576条件の梁診断と水・費用の収支であり、全粒や粒群床のシミュレーションではない。

Python 3でこのフォルダを作業ディレクトリにする。model.pyは標準ライブラリのみ、plot.pyはMatplotlibを使用する。

~~~text
rtk err python model.py
rtk err python -m pip install -r requirements.txt
rtk err python plot.py
~~~

- inputs.json：仮の形状・E・力・クリープ、継承した費用と運用条件。
- model.py：円形梁・有限回転拘束・支点移動、含水質量、円管毛管尺度、共通予算を計算。
- results.json：全結果。線形小変形の範囲表示と、接触前の表示を分離。
- verification.json：Hermite要素との独立照合、反力、IAPWS表1、収支の内部確認。
- plot.py／overview.png：適用範囲外の線を破線にした4図。
- requirements.txt：図の再現依存。
- sources.md：読めた範囲・読めなかった範囲と、次の設計判断。
- 検証記録.md：実行と公開前の確認記録。
- manifest.json：公開対象のパス・長さ・SHA-256。自身を除く。テキストCRLFをLFへ正規化し、PNGは元のバイト列を使う。

F=mπγdは指定した横力の尺度で、実液橋の上限ではない。L*は線形診断上の尺度で、凝集開始の実測閾値ではない。接合したことと剛な支点ができたことは別。数値確認・条件の数を独立した物理試験や成功確率に数えない。
