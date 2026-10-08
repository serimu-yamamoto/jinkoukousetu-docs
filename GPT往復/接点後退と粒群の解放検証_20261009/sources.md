# 出典・取得範囲

確認日2026-10-09。計算中の寸法・混合率・仮単価は本研究の仮定であり、文献の実測値とは分離する。

| ID | 資料 | 確認範囲と本計画への制限 |
|---|---|---|
| S1 | Haver et al., 2024, *Elasticity and rheology of auxetic granular metamaterials*, [DOI 10.1073/pnas.2317915121](https://doi.org/10.1073/pnas.2317915121)、[著者所属大学の公開版](https://pure.uva.nl/ws/files/248986951/haver-et-al-elasticity-and-rheology-of-auxetic-granular-metamaterials.pdf) | PDF全文抽出、Fig.4–5（本文p.4/PDF5）とFig.8–10（本文p.7/PDF8）の画像確認。寸法、拘束条件、50サイクルと速度記載差を照合。公表粒はcm級の2D実験。50℃・濡れたスキーの結果ではない |
| D1 | 同著者の[Zenodo 8405504](https://doi.org/10.5281/zenodo.8405504)と[追加データ10635094](https://doi.org/10.5281/zenodo.10635094) | 公開一覧でCSV・コードの存在を確認。今回はAPIとファイル取得が403で、原CSV・著者コードを取得できず、独立再解析は未実施。ファイルの存在を実行成功と数えない |
| S2 | Poincloux & Takeuchi, 2024, *Rigidity transition of a highly compressible granular medium*, [DOI 10.1073/pnas.2408706121](https://doi.org/10.1073/pnas.2408706121)、[著者公開原稿v2](https://arxiv.org/html/2404.09773v2) | Fig.5説明、式1とその導出、方法を確認。最終論文の識別子はPubMedでも照合。再計算は著者公開原稿の2D二粒モデルに限定。集団の閉じ込め、三次元、低摩擦域の未解決部分を残す |
| S3 | Djellouli et al., 2024, *Shell buckling for programmable metafluids*, [DOI 10.1038/s41586-024-07163-z](https://doi.org/10.1038/s41586-024-07163-z)、[著者公開PDF](https://bertoldi.seas.harvard.edu/sites/scholar.harvard.edu/files/bertoldi/files/nature_adel.pdf)、[研究室による図解](https://www.mrsec.harvard.edu/research/highlight_230.php) | 要旨と著者PDFの検索抽出部分・研究室説明を確認。独立粒内部の座屈という比較原理。液体中・油中の挙動を乾いた人工フィルンへ移植しない |

S1取得PDF：30,337,438 bytes、SHA-256 d79b1437b33de614be5f379b0285edd9525dbb9db6ea3a41069c0f1ce66f60a9。PDFに大学の表紙1ページが付くため本文ページ番号との差がある。全文・論文画像は再配布しない。数値を図からデジタイズしたとは主張しない。

既検討のフック粒 [Liu et al. 2026, 10.1126/sciadv.aec8845](https://doi.org/10.1126/sciadv.aec8845) は第7巡等の既出資料。今回は新発見として数えず、H56の引っ掛かりを増やさない比較対象とする。

検索で確認した連続補強格子と砂の研究 10.1016/j.taml.2026.100729 は要旨等の範囲。独立粒との拘束の違いを示す探索先にとどめ、数量モデルへ採用しない。
