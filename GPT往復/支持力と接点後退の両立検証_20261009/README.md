# 第57巡・支持力と接点後退の両立検証

[本文](../GPT回答_多方向探索第57巡_荷重を支える芯と解放する接点の統合_20261009.md) / [入力](inputs.json) / [数式と限界](model.md) / [出典](sources.md) / [未実施の試験計画](test_plan.json)

実物試験0件。成功確率未算定。逆算した仕様と計算の照合を収録。

- calculate.py: Python標準ライブラリで全計算表、results.json、validation.jsonを生成。
- draw.py: matplotlibで4組のPNG/SVGを生成。コードは必要ならリポジトリ直下の.depsを参照する。
- audit.py: 単位・計算値・リンク・履歴の保持・図の出力・文書の主張を照合。これは実物試験ではない。

| 表 | 内容 |
|---|---|
| hinge_force.csv | 仮係数別の曲げ部支持力 |
| required_modulus.csv | 曲げ部単独で荷重を支える場合の逆算係数 |
| architecture_comparison.csv | 局在曲げと分散曲げの代理比較 |
| core_clearance.csv | 芯断面・横膨張・退避の隙間 |
| load_control.csv | 線形芯の一定圧力下の平衡と可動域超過 |
| progressive_core.csv | 二段芯の逆算曲線と軟化の反例 |
| packing_counterexamples.csv | 充填が強くなると抜けない反例 |
| gas_core.csv | 理想気体の独立比較 |
| core_cost.csv | 芯だけの仮定材料量・価格 |

各CSVは観測データではない。物性・境界条件・価格はinputs.jsonとmodel.mdで出所を確認する。

再計算は、このディレクトリで python calculate.py、続いて python draw.py、python audit.py。初回計算後の検査を記録したvalidation.jsonとdocument-audit.jsonを同梱。4図は目視確認済み。

publication-manifest.jsonは自分自身以外の今回の公開対象について、パス・バイト数・SHA-256を保持する。公開後は固定コミットから全対象とマニフェスト自身を取得して原本照合する。照合記録は作業用Git管理領域に作り、作業用複製と一緒に削除する。
