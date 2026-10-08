# 第31巡 一次資料台帳

確認日：2026-10-08。根拠は5件の一次資料。取得した全文は再配布しない。著者の測定・掲載式・メーカー紹介・本計算の仮定を分離した。

| ID | 文献・参照先 | 確認した範囲 | 設計へ使わない外挿 |
|---|---|---|---|
| S1 | Tammaro et al. (2022), *Expanded Beads of High Melt Strength Polypropylene Moldable at Low Steam Pressure by Foam Extrusion*, Polymers 14, 205. [DOI](https://doi.org/10.3390/polym14010205) / [全文XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8747224/fullTextXML) / [出版社PDF](https://mdpi-res.com/d_attachment/polymers/polymers-14-00205/article_deploy/polymers-14-00205.pdf) | 工程・添加剤・密度定義、p.6 Table 1のCO₂系列をPDF画像でも照合。約20kg/hの実験装置。GMS・タルクの記述 | 成形板の強度を未接合の粒床へ使わない。潤滑剤・無機核剤入りの配合を本計画に採用済みとしない |
| S2 | Sulzer/Borealis, E10672 en 5.2024, ePP Foam Extrusion technology. [公式PDF](https://www.sulzer.com/-/media/files/products/sulzer-chemtech/brochures/english/epp_extrusion_technology_2_e10672_en_web.pdf) | 公式PDFの公開取得結果・p.2表：CO₂系列の粒径3–5mm、かさ密度35–120kg/m³、生産80–150kg/h | 一般製品紹介。価格・0.3–0.6mmへの生産能力・本用途性能の保証ではない。直接ダウンロードで404の場合あり |
| S3 | Tian et al. (2025), *Shortening the Saturation Time of PBAT Sheet Foaming via the Pre-Introducing of Microporous Structures*, Materials 18, 1044. [DOI](https://doi.org/10.3390/ma18051044) / [全文XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11901114/fullTextXML) / [出版社PDF](https://mdpi-res.com/d_attachment/materials/materials-18-01044/article_deploy/materials-18-01044.pdf) | p.5式(2)/(3)とL定義をPDF画像でも照合。指数の分母の4倍差を確認 | どちらを回帰に使ったかは不明。公表Dを修正して採用していない。厚板時間を小粒の実サイクルへ換算しない |
| S4 | Huang et al. (2022), PPビーズのCO₂押出発泡と風冷切断。Journal of CO₂ Utilization 64, 102167. [DOI](https://doi.org/10.1016/j.jcou.2022.102167) / [出版社](https://www.sciencedirect.com/science/article/pii/S2212982022002864) | 出版社公開の概要・工程説明。本文全体・補足データは未取得 | 製造方式の存在だけを引用。微粒径・歩留まり・価格・50℃性能を埋めない |
| S5 | Yuan et al. (2024), PLA/PBSの開孔発泡体。ACS Sustainable Chemistry & Engineering 12, 18101–18113. [DOI](https://doi.org/10.1021/acssuschemeng.4c06545) / [出版社](https://pubs.acs.org/doi/10.1021/acssuschemeng.4c06545) | 出版社の検索配信概要。6wt％PBS系列の発泡・開孔、鎖延長剤、油水分離用途。Crossrefで2024-12-03の刊行を照合 | 全配合・工程条件の再現確認は未了。pH13の分解を雨水中の安全・寿命へ、油吸着を滑走へ転用しない |

## 計算への入力

- inputs.json の source_observations：S1の表・装置容量、S2の掲載範囲、S3の式の分母を転記。±は原表の表示幅で、勝手に95％信頼区間とは扱わない。
- Dの3値、粒寸法・密度・充填率・皮厚、歩留まり、面積・厚さ・生産日数、年2％補充・50円/kgの許容固定費：すべて比較用仮定。
- 球・平板の拡散級数は本文で寸法と境界条件を定義。S3式(2)/(3)の片方をそのまま校正式として使っていない。球は独立した差分法でも照合。
- 表面濃度ゼロへの切替は理想脱離。実物の気泡生成、圧力履歴、加熱、結晶化、濃度依存D、外部物質移動抵抗は含まない。
- メーカーの「かさ密度」を個別粒の外形体積当たり密度へ転記しない。材料選択・品質の実証は0件。

## 取得版の記録

URLは上表。下記ファイルは確認用に取得し、GitHub照合後に作業コピーとともに削除。公開成果には本文・必要な入力数値と取得版ハッシュだけを残す。

| 確認用ファイル名 | bytes | SHA-256 |
|---|---:|---|
| epp2022.xml | 79378 | 086467a7514b746486a00f03ccdf4ddbcbb36aba774e97e4d0b677b7368c93b9 |
| epp2022.pdf | 1427335 | b0e715cc292b9c34bc5580509ef29e4e98bd6ebd7a70c8d3e654d35400551a37 |
| pbat2025.xml | 154970 | 8cb2bc44fde05289bdb29f0afbb253002c59fc0d4ca6d614e9100d04dcafe6bb |
| pbat2025.pdf | 4821420 | 7249453768be6419a278591cbd2aa3dd37c9c391069dfddecf86c1670987e7b6 |
