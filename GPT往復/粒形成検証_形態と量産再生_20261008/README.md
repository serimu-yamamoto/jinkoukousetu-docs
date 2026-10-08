# 第17巡 再現資料

[報告本文](../GPT回答_多方向探索第17巡_枝形状の形成と量産再生の成立条件_20261008.md)の計算・理想形状・出典を保存する。物理試験0件、実物成功確率null。

## 再現

Python 3環境でこのフォルダを作業ディレクトリにする。数値・形状の計算は標準ライブラリのみ。図にはrequirements.txtのMatplotlibを使う。

~~~text
rtk err python formation_model.py
rtk err python pulp_scale.py
rtk err python -m pip install -r requirements.txt
rtk err python plot.py
~~~

- inputs.json：熱物性・形状・運用・税抜仮予算。熱の継承値以外の粘度・表面張力等も未校正の感度入力。
- formation_model.py：熱量と毛管時間尺度、X17断面・切断・流量、再生単価上限を計算。results.jsonとverification.json、STL/SCADを生成。
- pulp_scale.py：現行参照SWP仕様と用途別Fybrel資料を分けて、含水原料・ADkg・乾燥kg・仮の被覆物量を計算。pulp_scale.jsonを生成。
- plot.py：overview.pngを生成。
- X17_reference_mm.stl／.scad：mm単位の理想参照形状。外径0.6mm、長さ0.3mm、720分割。切断端は丸めていない。製造ダイ・実物・粒間保持・安全の証明ではない。
- sources.md、探索台帳.md、検証記録.md：出典の適用範囲、比較判断、実行記録。
- manifest.json：公開時の成果ハッシュ。自身のハッシュは含めない。UTF-8テキストはCRLF→LF、PNGはバイト列をそのまま照合。

数値確認は、熱収支の別積分、断面積の解析式と多角形近似、閉メッシュ・向き・体積、切断個数と質量流量、年費の別計算である。条件数を独立した物理試験の件数や成功率にしない。局所の熱模型や固体断面から、雪状結晶・雪感・50℃耐久・耐候・安全を補わない。
