# 第104巡の再現資料
サーバー上で再現する。PCへの研究ファイル作成はしない。Python 3.14.4 / NumPy 2.5.0 / SciPy 1.18.0で実行。

```sh
python3 -B GPT往復/拡大流路と支持剛性の連成監査_20261010/reproduce.py --check
python3 -B GPT往復/拡大流路と支持剛性の連成監査_20261010/section_tradeoff.py --check
```

初回生成は `--check` を外す。公開資料では `計算部品/flared_ligament.py` を使用。作業時のみ同じ内容の `~/firn/lib/flared_ligament.py` を利用した。共有部品の選択は `FIRN_COMMON_LIB` で切り替える。

- [報告](../GPT回答_多方向探索第104巡_排水出口と支持剛性の両立条件_20261010.md)
- [inputs.json](inputs.json)：設定一覧。実行設定は再現スクリプト内の同値定数。
- [reproduce.py](reproduce.py)：24状態の解析、解析解照合、メッシュ比較。24物理試験ではない。
- [results.json](results.json)：全状態、解析式、メッシュ比較、部品ハッシュ。
- [validation.json](validation.json)：168件の数値確認。成功確率の母数にはしない。
- [section_tradeoff.py](section_tradeoff.py) / [section_tradeoff.json](section_tradeoff.json)：I、材料体積、原料費だけの条件。
- [claude_handoff.md](claude_handoff.md)：共有する検証依頼。
- [research_state.json](research_state.json)：実証0件／成功確率null／次の切り口。
- [manifest.json](manifest.json)：公開前の正確なバイト数・SHA256。自己参照を除く。
- [index_preservation.json](index_preservation.json)：6つの入口・台帳の旧本文保存確認。

## 数式と境界条件
Q4は[第94巡の要素定式化](../弾性根元と高温復元骨格の検証_20261009/reproduce.py)を再利用し、矩形から一般四辺形へ拡張。参照SHA256は結果に保存。2×2ガウス積分、平面応力、E=1、面外厚さ=1。根元全固定、上面の法線または横変位を高さの10⁻⁶に指定し、反力から剛性を計算。上端のもう一方の自由度は拘束しない。

深さs=z/ℓ、幅w(s)。一次元の比較式は
`K_axial/K0 = 1 / ∫[w_top/w(s)]ds`、
`K_bending/K0 = 1 / {3∫s²[w_top/w(s)]³ds}`。
後者はEuler–Bernoulli片持ち梁の端荷重近似であり、短い支柱のQ4横変位条件と同じ厳密解ではない。

スリット幅a(s)=0.625−w(s)、2本並列の局所流路近似は
`R_local/R0 = (0.25³/2)∫a(s)^−3 ds`。
抵抗基準は幅0.25・同深さの1本流路。入口や移行部の流れ場を解いた式ではない。

## 証拠の範囲
168件は計算整合性の確認。物理実験、臨床・安全評価、摩耗、雨台風後の回復、冬の定着、粒子集合体の3D力学、成功率の測定は実施していない。
最終2メッシュの差は0.025未満という判定を満たしたが、真の誤差の上限ではない。

## 一次資料
Gravelle et al. 2013, *Optimizing water permeability through the hourglass shape of aquaporins*。
[本文](https://arxiv.org/html/1310.4309v1)、[DOI](https://doi.org/10.1073/pnas.1306447110)。
2026-10-10に§§1–2を確認。入口形状の重要性の根拠に限り、ナノ孔の係数を本模型へ移植していない。
