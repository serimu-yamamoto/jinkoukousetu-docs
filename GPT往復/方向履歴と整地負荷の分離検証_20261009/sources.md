# 第93巡の一次資料と履歴

2026-10-09参照。原著の複製は保存せず、確認範囲・照合用ハッシュ・リンクを残す。原著値を人工粒の摩擦・摩耗係数へ入力していない。

| ID | 一次資料 | 確認範囲・今回の扱い |
|---|---|---|
| S1 | Dunn et al., [Spatial geometric effects on the friction coefficients of UHMWPe](https://research.me.udel.edu/~dlburris/papers/JA18.pdf), DOI 10.1016/j.wear.2007.05.012 | 第42巡の既読資料を再確認。本文と表2画像を照合。乾燥UHMWPE／CoCr、平均速度0.0508m/sで方向依存。表2の直線0.118とchirp0.270。本文と表1の温度記載に差があり、行ごとの温度を断定しない。50℃・実ソールの証拠ではない |
| S2 | Kang et al. (2008), [Quantification of the Effect of Cross-shear on the Wear of Conventional and Highly Cross-linked UHMWPE](https://pmc.ncbi.nlm.nih.gov/articles/PMC2239346/), DOI 10.1016/j.jbiomech.2007.09.005 | 第54巡の既読資料。本文・Appendix Aを再読。材料座標の回転と局所仕事が必要。UHMWPE／CoCr・血清系であり、屋外乾燥の係数に転用しない |
| S3 | Dressler et al. (2011), [Predicting wear of UHMWPE: Decreasing wear rate following a change in direction](https://www.epfl.ch/labs/tic/wp-content/uploads/2018/10/science8.pdf), DOI 10.1016/j.wear.2011.06.006 | 今回新規照合。全文、p.2880の方法・表1・図2を画像確認。架橋PE二種／CoCr、37±1℃・血清、滑走330N・回転30N。90°変更間の累積滑りを比較。5〜100mmで1周期摩耗は距離比例にならず、XLK群では全群比較の有意差が出ない。微視機構は未測定。原著のピン寸法mm／inchは不整合のため採寸に使わない。指数減衰式や人工粒のℓを本論文の測定値としない |
| S4 | Dreyer et al. (2022), [Anomalous Wear Behavior of UHMWPE During Sliding Against CoCrMo Under Varying Cross-Shear and Contact Pressure](https://link.springer.com/article/10.1007/s11249-022-01660-w) | 今回新規照合。出版社HTML方法・結果・考察。37℃血清、滅菌UHMWPE／CoCrMo。多方向で摩耗増だが非零CS内の単純な相関はなく、接触圧も変数。ひとつのCSから寿命を決めない根拠 |

取得PDFのSHA-256：S1 `e1b90aab5c970839f10c599f1c119bec2d3aba491bfae8091d3c1f6e3fefe2ed`、S3 `664dad69eebc2805089a7babf684a35a4fc36dfa1c0922cec68ad7468b19ebd2`。原著図は閲覧確認のみで成果へ転載していない。

## 既存研究からの差分

- [第42巡](../GPT回答_多方向探索第42巡_摩耗後も滑りを保つ先端と接触相の配置_20261009.md)：摩耗面の再配置、未知の摩耗倍率χと接触面数M。
- [第54巡](../GPT回答_多方向探索第54巡_雪に接する面の微細構造と回転摩耗_20261009.md)：材料座標と方向行列。今回はその集約指標に時間順序・変更間隔が残らない点を具体化。
- [第89巡](../GPT回答_多方向探索第89巡_慣らした板だけに依存しない滑走接点_20261009.md)：板と材料双方の慣らし。今回も対向面履歴を交換・混用しない。
- [第92巡](../GPT回答_多方向探索第92巡_離型性と滑走性を分けたPMP複合枝の検証_20261009.md)：MD/TDを別試片で測るだけでは同一接点の方向変更履歴を測れない。
- Claudeの[物性照合台帳](../../調査台帳/物性値照合_自律ループv2v3.md)はLFハッシュ `054c9388de3be3bd251c395059a9e02c9d3b336885236683ba3f528ff819d71f`。開始commit `6eda59ccd678f3d5aee302dcbbf6e661aa36a5ed`時点で前巡と同一。v3全結果・元コード・新しい実測は未確認。
