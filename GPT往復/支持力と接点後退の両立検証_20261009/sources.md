# 第57巡の一次資料・参照範囲

閲覧日: 2026-10-09 JST。以下は他者の研究であり、H57の実験結果ではない。既存資料からの継承と今回の追加を分ける。

| ID | 一次資料 | 確認した範囲・使い方 | 転用できないもの |
|---|---|---|---|
| S1 | Cirelli et al., 2025, [Second-Order Kinematic Invariants for the Design of Compliant Auxetic Symmetrical Structures](https://doi.org/10.3390/sym17010134)。[著者機関PDF](https://art.torvergata.it/retrieve/e8d7805a-795c-47a0-afd9-a395137f07cf/AuxeticCompliant_Symmetry-17-00134.pdf) | 全文の検索提供テキスト、式2・12–14、§5.2–5.3を確認。回転ばねの剛性と変形の設計を区別する参考。実験での力比較は行っていない旨を確認。 | H56の寸法・境界条件と異なる。著者の力式をそのまま実装していない。PDF直接取得はHTML応答、画像表示はcache miss。図の画素照合・独立追試はできていない。 |
| S2 | Titchener-Hooker et al., 2026, [Mechanism-Driven Design and Validation of a Multi-Material Polymeric Auxetic for Deformation-Activated Sealing](https://doi.org/10.3390/jmmp10090327)。[著者機関書誌・要旨](https://research.birmingham.ac.uk/en/publications/mechanism-driven-design-and-validation-of-a-multi-material-polyme/) | 要旨・出版情報を確認。柔軟な形状変化部と荷重伝達部を組み合わせる機構の参考。 | 構造高さ6 mm・支柱厚さ1.25 mmの例。約22 kPaは封止性能であり、雪状粒床の支持圧力ではない。原著PDFは403で未取得。配合・安全性・50℃耐久を採用した根拠にしない。 |
| S3 | Kasgoz, 2021, [Mechanical, Tensile Creep and Viscoelastic Properties of Thermoplastic Polyurethane/Polycarbonate Blends](https://doi.org/10.1007/s12221-021-0113-z) | 出版社の要旨を確認。3 MPaの引張クリープを30/40/50℃で調査。PC添加の剛性増加と靭性低下の両面が示される。 | 有料本文は未取得・購入なし。本検証の圧縮係数・回復時間・湿潤疲労の値には使わない。要旨のクリープ低減率を50℃単独の数字として採用しない。 |

S1のモデルに関する記述は設計の考え方を参照したもの。本モデルの F=dU/dδ、芯の並列合成、固定中心の隙間と価格換算は独自の仮定計算。S1の式12に現れる有限変位と仕事の関係を、本モデルの瞬時力と取り違えない。著者のモデルや実験を再現・訂正したとは主張しない。

## 継承した研究

- [第56巡](../GPT回答_多方向探索第56巡_接点が縮んで抜ける粒と雪の支えの両立_20261009.md): H56運動学、一定圧力と一定変位の区別、粒群の解放、製造公差。
- [第53巡](../GPT回答_多方向探索第53巡_一体発泡で戻る粒と量産の成立条件_20261009.md): 多孔中心と緻密部。密度218 kg/m³を費用感度の仮値に再利用する。H53の粒数・外形・50℃物性をH57に移していない。
- [第55巡](../GPT回答_多方向探索第55巡_摩耗面の再生と材料交換を両立する設計_20261009.md): 再生と材料補充の区別、選別と処理能力。
- Claudeの[自律ループv2 第1〜4ラウンド](../../バーチャル試験/自律ループv2_噴霧結晶化素材_第1〜4ラウンド_20261008.md)、回覧板、READMEを継承。公開前にmainを再取得し、1edec668以降のClaude更新がないことを確認した。v3の完了結果・稼働・受領は未確認。

一次資料3件はいずれも本リポジトリの既存MarkdownをDOI検索した時点で一致なし。文献を増やしたこと自体を実証の増加には数えない。論文本文・図の複製は成果物に含めない。
