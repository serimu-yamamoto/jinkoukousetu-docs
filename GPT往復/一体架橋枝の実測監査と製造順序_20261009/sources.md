# 第95巡の一次資料と適用範囲

確認日：2026-10-09。原論文は転載しない。第42・54・93巡にも架橋PEの摩耗研究はある。今回の追加は50℃原表の分母監査、異なる架橋法の反証、端材回収を先行する工程収支。

## S1 — Burger / Fourie, 2005

[論文HTML](https://scielo.org.za/scielo.php?pid=S2309-89882005000100002&script=sci_arttext) / [原PDF](https://scielo.org.za/pdf/rd/v21/02.pdf)。The Impact of the Gamma Irradiation Dose During Sterilisation and Crosslinking on the Creep Properties of Ultra High Molecular Weight Polyethylene, R&D Journal 21(1),19–25。

Chirulen UHMWPE、8MPa圧縮、20mm試片。125kGyガンマ線・アセチレン雰囲気の比較。p24 Table7.1を画像で確認し、室温0.79→0.58mm、50℃1.26→0.80mm、60℃1.536→0.84mmを転記。表のDifferenceは架橋後値を分母とする。未処理比の減少率へ換算が必要。方法欄の1時間と図の約2時間には不整合があり、4時間保証・除荷後復元率には使わない。著者自身が統計的設計値としての限界を明記。電子線処理HDPEへの数値移植は不可。

取得PDF SHA256: 2ab8b0e0fa899cc5d024a136ffbbe224c876c7a5dc9a70ae842de91d0c39f3b6。原PDF・確認画像は作業用で、公開後削除。

## S2 — Svoboda et al., 2021

[DOI](https://doi.org/10.1098/rsos.202250) / [著者所属大学の全文PDF](https://publikace.k.utb.cz/bitstream/handle/10563/1010303/Fulltext_1010303.pdf?isAllowed=y&sequence=1)。Study of crystallization behaviour of electron beam irradiated polypropylene and high-density polyethylene, Royal Society Open Science 8:202250。

HDPE HTA002とPPを比較。30–120kGy電子線。HDPEのクリープ改善を示すFig1は200℃・0.1MPa。Fig3のDMAは融点以下で大差がなく、60–120℃で小幅な差。Fig6の結晶化度は再加熱後の値で、初期製品の50℃性能ではない。200kW/10MeVは使用装置仕様。処理時の冷却・搬送・線量分布を省いて能力換算しない。分子内の結晶変化から外形の雪状樹枝生成は導けない。

[Dryad付属データ](https://datadryad.org/dataset/doi:10.5061/dryad.dv41ns1wx)：APIでversion107648、ファイル598022、665503bytes、CC0を確認。配布元SHA256 9e9ed2532c07b82e58486d8fe29a755ceb2a382cc128ff715baa75ab352f378e。ファイル本体はAPI認証要求、通常公開リンクはHTTP403で取得できなかった。**Excel内容の読取・50℃数値抽出・再解析は未実施**。ハッシュは配布元メタデータであり、本体照合済みではない。認証回避や数値補完は行っていない。

## S3 — Montoya-Ospina et al., 2022

[出版社全文・DOI10.1002/pen.26178](https://4spepublications.onlinelibrary.wiley.com/doi/10.1002/pen.26178)。Effect of cross-linking on the mechanical properties, degree of crystallinity and thermal stability of polyethylene vitrimers。

MAHグラフトPEを4,4′-dithiodianilineで動的架橋。§3.7/Fig9：HDPE-V0.6は50℃・5MPaで未処理HDPEより初期変形が大きく、10⁴秒以降のクリープ速度は同じ。再加工できる化学系でも耐変形目的に直結しない反例。全ビトリマーを否定する根拠ではない。DTA系を人体・屋外安全確認済みの採用処方にしない。

## S4 — Gencur / Rimnac / Kurtz, 2006（online2005）

[PubMed・原著抄録](https://pubmed.ncbi.nlm.nih.gov/16303175/) / [DOI10.1016/j.biomaterials.2005.09.010](https://doi.org/10.1016/j.biomaterials.2005.09.010)。Fatigue crack propagation resistance of virgin and highly crosslinked, thermally treated ultra-high molecular weight polyethylene。

GUR1050、100kGyガンマ線後110℃または150℃・2時間熱処理。架橋材のき裂発生・進展抵抗低下を報告。今回の微細枝の寿命や50℃乾式スキー摩耗量には換算しない。全文ではなく抄録を確認。

## 参照した既存共有資料

- [第94巡](../GPT回答_多方向探索第94巡_高温復元骨格の候補と根元配置の成立条件_20261009.md)：75µm異材根元の量産・接合が未確認。今回の一体PE案はこの工程を減らす比較案。
- [Claudeの物性台帳](../../調査台帳/物性値照合_自律ループv2v3.md)：LF正規化SHA256 054c9388de3be3bd251c395059a9e02c9d3b336885236683ba3f528ff819d71f。前巡以降の変更なし。全結果・元コード・現在の稼働は未確認。

文献の有効性と、今回の製品が成立することは別々に判定する。
