# 第77巡の再現資料

[報告書](../GPT回答_多方向探索第77巡_滑走接点の発熱を抑える分割と荷重集中の反証_20261009.md)を先に読む。H77-Sは仮説・計算段階。物理試験0、成功確率未算定。

- [入力](inputs.json)、[式と適用範囲](model.md)、[再計算Python](reproduce.py)
- [集計](summary.json)、[32項目の照合](checks.json)、[収束](convergence.csv)
- [単独接点熱](thermal_sensitivity.csv)、[高さと荷重](height_load_cases.csv)、[連続熱](array_memory.csv)、[高さ誤差との複合](coupled_array.csv)
- [連続通過の時間履歴](array_traces.csv)、[法線支持荷重](normal_load_budget.csv)、[材料費感度](cost_sensitivity.csv)
- [比較図1](thermal_and_tolerance.png)、[比較図2](memory_and_material.png)
- [出典・参照証跡](sources.json)、[未実施仕様](test_matrix.json)、[Claude依頼](claude_handoff.md)、[判断](decision.json)
- [成果一覧とハッシュ](manifest.json)、[文書照合](document_audit.json)

## 再計算

Python 3、numpy、matplotlibを用い、このフォルダで python reproduce.py を実行する。requirements.txtは今回使用したバージョンを記録。ネット接続も旧巡の実行も不要。入力はinputs.json、出力は同じフォルダ。既存出力を上書きするため検証用コピーで実行する。数値比較の浮動小数差と図PNGのライブラリ差はあり得る。

277表行には収束9行を含み、時間履歴表は別。32照合は数学・実装の確認で、材料の実証ではない。図の英語表記、単位と範囲はmodel.mdで定義。

原著PDF・抽出本文・描画した原著ページは著作権のある参照資料として再配布しない。URL・取得サイズ・SHA-256と確認箇所をsources.jsonに残す。公開後に作業用PDF、依存環境、研究クローンと.gitを削除する。ルートの接続案内・利用設定を保持する。
