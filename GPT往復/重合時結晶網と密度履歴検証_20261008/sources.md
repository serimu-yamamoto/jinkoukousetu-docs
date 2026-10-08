# 第29巡 出典台帳

閲覧日2026-10-08。一次資料8件。実験は各著者による別用途のもの。著者のデータとH29の未実証の提案を分ける。第三者のPDF・SEM画像・全文は再配布しない。

| ID | 一次資料・参照箇所 | 確認した範囲／採用上の制限 |
|---|---|---|
| S1 | W. Zhang et al., [Particle morphology, structure and properties of nascent ultra-high molecular weight polyethylene](https://doi.org/10.1098/rsos.200663), R. Soc. Open Sci. 7, 200663 (2020)。[PMC全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC7481705/)、§3.1、表1、図1 | 原粉体の形態・密度を使用。流動試験の液体パラフィンは材料へ採用しない |
| S2 | V. A. Tuskaev et al., [Titanium(III, IV)-Containing Catalytic Systems for Production of Ultrahigh Molecular Weight Polyethylene Nascent Reactor Powders, Suitable for Solventless Processing—Impact of Oxidation States of Transition Metal](https://doi.org/10.3390/polym10010002), Polymers 10(1), 2 (2018巻、2017-12-21オンライン)。[PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6414873/)、[出版社PDF](https://mdpi-res.com/d_attachment/polymers/polymers-10-00002/article_deploy/polymers-10-00002.pdf)、表1、図5・6 | XMLとPDFを照合。低密度の群と高密度の別条件を区別。PDF p.8の形態図を目視。量産性・無残留・人体安全・スキー性能の資料ではない |
| S3 | F. Christakopoulos et al., [Solid-state extrusion of nascent disentangled ultra-high molecular weight polyethylene](https://doi.org/10.1002/pen.26787), Polymer Engineering & Science (2024)。§2.1、表1、§3.1、図3 | 全文HTML。粉体の密度と固相加工を区別。成形品や配向品の力学性能を未加工粉体床に転用しない |
| S4 | Celanese, [GUR UHMW-PE Overview](https://www.celanese.com/-/media/Engineered-Materials/Files/Brochures/GUR-015-UHMW-PE-Overview-PM-EN-r1-0916.pdf), GUR-015、r1-0916、印刷pp.30–31（PDF16枚目） | PDF表を目視して列対応確認。GUR2122／4120の代表値。2016年版で現行供給・価格保証ではない。HDTは成形試験片の条件付き値 |
| S5 | G. Yilmaz and E. Uslu, [A new approach for high-quality production of UHMWPE by applying powder vibration densification before sintering](https://doi.org/10.1016/j.powtec.2023.118741), Powder Technology 427,118741 (2023) | 出版社の要旨・公開プレビューを確認、全文未取得。振動が密充填へ使われる事実のみ使用。最適振幅・周波数を本設計へ転用しない |
| S6 | [WO2022049016A1: Ultra-high molecular weight polyethylene polymers having improved processability and morpology](https://patents.google.com/patent/WO2022049016A1/en) (2022公開) | 原開示の目的・粉体形態を参照。低絡み合い粉体は既存技術。権利存続や実施自由の判定には使用しない |
| S7 | B. J. Briscoe, V. Mustafaev, D. Tabor, [Lubrication of polythene by oleamide and stearamide](https://doi.org/10.1016/0043-1648(72)90314-6), Wear 19(4),399–414 (1972) | 出版社要旨を確認、全文未取得。LDPE平板／鋼・ガラス、表面被覆と移行の条件。45℃処理後の室温測定を50℃摩擦と誤読しない |
| S8 | TechnoAlpin, [SNOWMASTER, 2023 updates](https://www.technoalpin.com/pl/about-us/news/snowmaster-2023-updates-make-the-right-decisions-for-your-energy-consumptions/) (2023-10-06) | メーカーの全系統・給水・造雪機の電力指標の区別。費用単価や夏季の性能値には使用しない |

## 取得と精度の記録

PMCのS2ページは一時アクセス確認画面を返したため、Europe PMCの同一論文XMLと出版社PDFで本文・表を確認した。最初のMDPI /pdf URLはHTML応答だったので、PDFとして採用せず出版社配布PDFを取り直した。

S4の数表は文字抽出だけでなく、PDFの画像表示で確認した。S2は本文で50〜90 kg/m³と述べる一方、表1の別条件entry13／14／22／23は310／450／260／380 kg/m³。入力ファイルの範囲値は低密度群の範囲で、全試料の範囲ではない。

S3の低絡み合い原粉はS2と別材料。固相成形に用いた装置の高温・高圧と、50℃の開放粉体床の耐久を同一視しない。S4のHDT値をS2へ代入していない。

閲覧ファイルのSHA256は下記。研究結果を再計算するための入力ではなく、参照版の識別用である。

- nascent2017.xml: b6e26f992a0161aee19d7eeedc6f7598eadd3f753951623931651571fb74fe72
- nascent2017.pdf: 31c09219b9b67df659efc91dc80d6a9834fca9fae7a192363f014eda46ec5384
- gur.pdf: bb7ba789a952d40d88b4d6cd14e64eeafeff1e29684225e2be520edebf9e187e
