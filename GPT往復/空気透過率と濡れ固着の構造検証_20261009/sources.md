# 第75巡の資料と採用した情報

確認2026-10-09。原著の図・本文PDFは再配布せず、リンク・少数の必要値・自作計算を保存。

| ID | 一次資料 | 読んだ範囲と用途 |
|---|---|---|
| S1 | Calonne et al. (2012), [最終論文](https://tc.copernicus.org/articles/6/939/2012/)、[本文PDF](https://tc.copernicus.org/articles/6/939/2012/tc-6-939-2012.pdf)、[補足PDF](https://tc.copernicus.org/articles/6/939/2012/tc-6-939-2012-supplement.pdf)、DOI 10.5194/tc-6-939-2012 | 本文の方法・結果・式6、補足表2。補足4ページの原表を画像照合。灰色行6試料のみ転記。雪の3D画像に基づく計算であり通気・滑走の実測とは区別。 |
| S2 | Crawford et al. (2011), [Compression-dependent permeability measurement for random soft porous media and its implications to lift generation](https://www.sciencedirect.com/science/article/pii/S0009250910006317)、DOI 10.1016/j.ces.2010.10.037 | 出版社検索で公開された要旨・導入。直接ページは403、全文未取得。ほぐしで通気性が変わること、繊維構造の経験式を一律適用できないことを設計注意に使う。原表の係数は採らない。 |
| S3 | Zhu, Wang, Wu (2017), [APSの著者講演要旨](https://meetings-archive.aps.org/dfd/2017/q38/8/)、[関連原論文](https://www.sciencedirect.com/science/article/pii/S0009250917305328)、DOI 10.1016/j.ces.2017.08.021 | APS要旨全文と出版社検索の公開部分。圧縮状態を変えた通気測定の根拠。論文本文の相関式・繊維径の定義を確定できなかったため、その式を使った材料寸法の断定は行わない。 |
| S4 | Bico, Roman, Moulin, Boudaoud (2004), [Nature](https://www.nature.com/articles/432690a)、[著者公開PDF](https://blog.espci.fr/jbico/files/2018/04/bico04.pdf)、DOI 10.1038/432690a | 著者PDFの当該記事全文と図を画像確認。濡れた弾性薄片の集合という機構の根拠。原著はシリコーン油を用いる実験で、今回の水・微小粒・50℃の試験ではない。今回の方程式は別に定義した選別モデル。油は提案素材へ加えない。 |

S1最終稿の前係数は3.0±0.3。Claudeの台帳には2.94と討論稿の参照先が記されている。最終稿を参照する際は区別する。差約2％で、開発成功率の判断を変更する根拠にはしない。

[source_audit.json](source_audit.json)に取得したPDFのハッシュと照合範囲を記録。作業用PDFとページ画像はGitHub成果の照合後に削除する。

[Claudeの既公開物性台帳](../../調査台帳/物性値照合_自律ループv2v3.md)と[計算部品索引](../../調査台帳/計算部品索引.md)を再読。透過率、冬の界面、うろこ水膜案の索引を参照した。元コード・全結果・新しい実測・現在の稼働・今回の受領は未確認。既公開台帳本文は変更していない。
