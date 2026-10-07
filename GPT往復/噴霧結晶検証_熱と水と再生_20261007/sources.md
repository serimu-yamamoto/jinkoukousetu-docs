# 出典と適用範囲

参照2026-10-07〜08。原著・メーカー・大学計算表・一次特許を区別する。文章・図の転載は行わず、研究への適用範囲を記録する。

| ID | 出典 | 今回使った点／使わない推論 |
|---|---|---|
| S1 | [PRECI: About Spray Cooling](https://www.preci.co.jp/en/technologies/about-spray-cooling/) | メーカーの工程説明。球状粒、熱除去、供給・回収を確認。指定樹脂の30℃製造能力・価格・雪感の保証ではない |
| S2 | [HDPE複合材DSC、表2、DOI 10.1002/app.70796](https://onlinelibrary.wiley.com/doi/full/10.1002/app.70796) | 公開検索で得たHDPE行はTm131.2℃、Tc113.5℃、融解159.6J/g。本文全体はセキュリティ確認画面で未取得。銘柄の50℃設計物性へ外挿しない |
| S3 | [La Bella et al., 2023, J. Appl. Cryst., 10.1107/S1600576723002881](https://pmc.ncbi.nlm.nih.gov/articles/PMC10241062/) | 水和に伴う溶解・析出の原著。浸漬毛細管で構造を観察。屋外噴霧、60分養生、安全、雪状応答は未検証 |
| S4 | [Bremen: Solubility of different evaporite minerals](https://www.sedgeochem.uni-bremen.de/solubility.html) | 25℃純水、PHREEQC 2.12.5/PITZER計算表。石膏2.617g/L、方解石0.052g/L（大気CO₂条件）。実流出水・冬の飽和濃度・速度測定ではない |
| S5 | [Spray-Congealing and Wet-Sieving...](https://pmc.ncbi.nlm.nih.gov/articles/PMC8217042/) | マンニトールの噴霧粒化原著。冷却塔−10℃の条件と球状粒。暖気で雪状床が成立する根拠にしない |
| S6 | [EP3259328B1](https://patents.google.com/patent/EP3259328B1/en) | PEG装飾雪の一次特許。滑走用雪の独立実証ではない |
| S7 | [US3950293](https://patents.justia.com/patent/3950293) | ポリオレフィンのフィブリド工程の先行例。溶媒を含む製造を、溶媒なしの屋外噴射へ読み替えない |
| S8 | [EP2402411A1](https://patents.google.com/patent/EP2402411A1/en) | 粉砕発泡PEの人工雪特許。外観・舞台用途と滑走床を区別 |
| S9 | [Claudeの方針更新8523343](https://github.com/serimu-yamamoto/jinkoukousetu-docs/commit/852334301f6c7f0952b929d3c752bd5d2bd49474) | 噴霧結晶化へ重点を戻す記録。新しい物理実験や「全物質を網羅済み」という証拠は含まれない |

密度950kg/m³、cp=2.3kJ/(kg K)、樹脂k=.3W/(m K)、空気k=.028W/(m K)、Nu=2/4/8、蒸発潜熱2.45MJ/kg、価格・稼働日・濃度等は比較用の定数・仮定。製品仕様ではない。S2の融解エンタルピーを冷却にも流用する近似を採用したため、核生成・結晶化速度を必要入力として残す。

外部サイトへの照会送信、購入、実験はしていない。検索や閲覧の記録を成功試験として数えない。取得できなかった検索処理は証拠へ追加しない。


## S9：別の結晶相・複合化

Steinacker et al. (2024), DOI 10.3390/jfb15040108。[原著](https://www.mdpi.com/2079-4983/15/4/108)。方法2.1〜2.3と結果3を出版社ページで確認。初期硬化と養生後の強度、酸調製と洗浄、溶出・相変化を区別。詳細は[比較追記](別結晶接点の比較追記.md)。屋外性能・雪感・50℃・安全の証拠にはしない。
