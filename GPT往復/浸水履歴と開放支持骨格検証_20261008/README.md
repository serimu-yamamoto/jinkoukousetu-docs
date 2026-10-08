# 第30巡 再現資料：浸水履歴と開放支持骨格

[本文へ戻る](../GPT回答_多方向探索第30巡_浸水履歴と開放支持骨格の設計_20261008.md)

## 内容

| ファイル | 内容 |
|---|---|
| [inputs.json](inputs.json) | S1の5行、仮想孔・接続・気体・工程条件と適用限界 |
| [calculate.py](calculate.py) | Python標準ライブラリによる全計算、22項目の照合 |
| [results.json](results.json) | 30圧力履歴、2接続例、18気体条件、4工程量条件、短絡計算 |
| [validation.json](validation.json) | 保存則・数式・接続探索等の照合。材料の合格試験ではない |
| [plot.py](plot.py) | 下記2図の再生成 |
| [figure1_wetting_history.png](figure1_wetting_history.png) | 膜の測定値と未校正短絡、仮想孔の濡れ履歴 |
| [figure2_structure_and_process.png](figure2_structure_and_process.png) | 接続反例、気体圧、前処理を含む工程量 |
| [sources.md](sources.md) | 一次資料6件、確認範囲・入力出所・取得版ハッシュ |
| [publication-manifest.json](publication-manifest.json) | 本文・再現資料・共有入口の保存照合用ハッシュ |

## 再計算

Python 3.10以降。計算本体は追加依存なし。図だけmatplotlibとnumpyが必要。作業時はmatplotlib 3.11.2を使用した。Pythonの生成JSONはUTF-8・LFを明示して保存する。

~~~text
python calculate.py
python plot.py
~~~

calculate.py は本フォルダの結果・照合JSONを更新する。plot.py は本フォルダのPNGを更新する。入力値変更後は両方実行する。プロジェクトのRTK運用対象環境では、上記実行をRTK経由にする。

## 照合の意味

22項目：IAPWSの丸め基準2件、径逆比例・角度符号・90°、履歴4件、同一孔分布・接続差・独立探索2件、気体保存・初期値・仕事微分2件・計算域、工程の供給量・全段計上・歩留まり・面積比例。22/22は物理試験の成功率ではない。

結果の physical_tests は0、physical_success_probability はnull。未測定値に確率分布を割り当てて90％へ上げる処理は存在しない。圧力サイクルは時間軸ではなく、負圧の操作や50℃での滑走を実行した記録でもない。

## 保存方針

GitHub mainへ保存後、不変コミットのraw内容をローカルとバイト単位・SHA-256で照合する。manifest自身は自己参照できないため自身の一覧から除外し、別途raw照合する。照合完了後、ローカル研究コピーとGit履歴、取得した第三者資料・図生成依存を削除。接続案内と既存設定は保護する。
