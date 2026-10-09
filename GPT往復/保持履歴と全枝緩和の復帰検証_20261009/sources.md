# 第96巡 出典と使える範囲

確認日：2026-10-09。一次資料の知見と本稿の仮模型を分離する。論文の原図・本文・PDFをこの資料倉庫へ転載しない。

| ID | 一次資料 | 確認した範囲 | 採用・不採用 |
|---|---|---|---|
| S1 | Gomez, Moulton, Vella (2019), Dynamics of viscoelastic snap-through, JMPS 124, 781–813. [DOI](https://doi.org/10.1016/j.jmps.2018.11.020)・[著者稿](https://people.maths.ox.ac.uk/moulton/Papers/GMV18_LargeDeSnap_Resub.pdf) | 著者稿本文、§2–3、式3–9。PDFの式3/5を描画確認 | 荷重保持と慣性を含む模型の出発点。原模型は垂直部だけSLS、斜材は弾性。本巡の全材SLSは独自拡張であり論文の実証結果ではない |
| S2 | Liu et al. (2021), Effect of imperfections on pseudo-bistability of viscoelastic domes, EML 49, 101477. [DOI](https://doi.org/10.1016/j.eml.2021.101477)・[著者所属機関PDF](https://smart.hit.edu.cn/_upload/article/files/15/97/be9e866a4167a0588f12fd1b56b1/90f40a3f-e682-4b20-8066-ef4a43831c05.pdf) | 要旨・本文§1–2と方法を確認 | 小さい形状欠陥でも遅延・安定性が変わる。試料はSylgard184の15:1配合。シリコーンを候補に追加する意味ではなく、PEの50℃係数へ転用しない |
| S3 | Che, Rouleau, Meaud (2019), Temperature-tunable time-dependent snapping of viscoelastic metastructures with snap-through instabilities, EML 32, 100528. [出版社](https://www.sciencedirect.com/science/article/pii/S2352431619300161)・[著者掲載一覧](https://sites.gatech.edu/meaud/publications/) | 一次資料の要旨・書誌を確認。温度別の全データは未取得 | 温度が遅延を変える根拠。特定PEの50℃復帰時間は得ていない |
| S4 | Liu et al. (2026), 3D self-locking granular metamaterials, Science Advances 12, eaec8845. [PubMed](https://pubmed.ncbi.nlm.nih.gov/41961926/)・[公開全文XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13068065/fullTextXML) | 公式Europe PMC XML全文、粒構造・せん断・繰返し試験 | TPUフックと樹脂本体の接着組立。粒間の滑り後の係合、繰返し時の残留変形を区別。100回の圧縮と低損傷を、完全自動復元やスキー寿命と読み替えない |

S1とS4は[第7巡](../GPT回答_多方向探索第7巡_雪の滑走応答と可逆接点の設計条件_20261007.md)ですでに参照済み。新発見とは扱わない。本巡の追加は、S1の数値実装、斜材の緩和を含めた比較、寸法の最悪組合せ、復帰判定の監査である。S2は小欠陥の影響の根拠に限定し、そのドームの限界値を本模型へ移植しない。S3の温度依存係数も未導入。

取得時照合：S1著者稿PDF SHA-256 f023efb4eae972d99d58bf5590659213052e2d9943362d7d595413e23a9162de、S4 XML SHA-256 3cf3f574f7ff26d244a5d0a83df2ab74d0543d0b03eb4fa9ceaa27e4054d8bb8。これは取得物の同一性であり、主張の正しさの認証ではない。S2のローカル取得はタイムアウトしたが、公開PDFを閲覧して方法を確認した。S2のローカルハッシュはない。

S4の摩擦係数0.49–0.55はその粒接触条件であり、スキー摩擦へ入力しない。孔隙率表記も別途定義照合が必要なため本計算に使わない。いずれも完成材の人体・環境安全性を保証しない。
