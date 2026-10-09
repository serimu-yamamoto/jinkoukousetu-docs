# 第74巡の一次資料と使用境界

確認日2026-10-09。全文の転載・著者図の再配布は行わない。図と計算は本調査の仮説に基づく。本文中のS番号は以下に対応する。

| ID | 一次資料 | 今回確認した範囲 | 使用境界 |
|---|---|---|---|
| S1 | Zhu, Weinbaum, Wu (2019), Experimental study of soft porous lubrication, [DOI 10.1103/PhysRevFluids.4.024305](https://journals.aps.org/prfluids/abstract/10.1103/PhysRevFluids.4.024305)、[APS受理原稿](https://link.aps.org/accepted/10.1103/PhysRevFluids.4.024305) | 受理原稿全文7 PDFページ。Fig.2・Table Iのページを画像でも確認 | 空気潤滑の実験的先行例。側面を封じた繊維シートで、提案中の自由粒ではない。数値の核心は報告本文、限定した速度5行は source_speed_subset.csv |
| S2 | Wu et al. (2005), Dynamic compression of highly compressible porous media with application to snow compaction, [Cambridge](https://www.cambridge.org/core/journals/journal-of-fluid-mechanics/article/abs/dynamic-compression-of-highly-compressible-porous-media-with-application-to-snow-compaction/C60C20FA1FC965F9E4ECD25319F7A5AF)、[DOI](https://doi.org/10.1017/S0022112005006294) | 出版社の要旨。本文の数表は今回未照合 | 雪のピストン圧縮で空気と固体の力を分離し、排気・回復を扱った先行例。実斜面のスキー摩擦へ転用しない |
| S3 | Crawford et al. (2012), Experimental study on the lift generation inside a random synthetic porous layer under rapid compaction, [大学登録資料](https://pure.psu.edu/en/publications/experimental-study-on-the-lift-generation-inside-a-random-synthet/)、[DOI](https://doi.org/10.1016/j.expthermflusci.2011.09.014) | 大学の要旨と出版社検索結果。直接アクセスに制約があり全文未照合 | 合成繊維の急速圧縮という別系統の測定例。物性の数表は本計算に取り込まない |
| S4 | Zhu, Nathan, Wu (2018), An experimental study of the lubrication theory for highly compressible porous media, with and without lateral leakage, [大学登録資料](https://pure.psu.edu/en/publications/an-experimental-study-of-the-lubrication-theory-for-highly-compre/)、[DOI](https://doi.org/10.1016/j.triboint.2018.06.016) | 大学の要旨。出版社本文未取得 | 横漏れの有無を区別した実験があるため、本調査でも封止条件を流用しない。提案粒の低摩擦の証拠ではない |
| S5 | Zhu, Nathan, Wu (2019), Multi-scale soft porous lubrication, [大学登録資料](https://pure.psu.edu/en/publications/multi-scale-soft-porous-lubrication/)、[DOI](https://doi.org/10.1016/j.triboint.2019.05.003) | 要旨と出版社公開部分 | 厚さと固体支持が関わる研究。薄い層を都合よく扱うだけの設計を避ける補助資料。未知の固体定数を推定しない |

S1のPDFは取得時1,577,509 bytes、SHA256 282bfef03073b13b5b9c75c8deacecb6e0e2447c5b2bce7f2c0ff4b21164b302。検証後に作業用PDFとページ画像を削除する。保存するのは書誌・照合箇所・必要な数値・自作コード。

[出典の速度5行](source_speed_subset.csv)の比 μ/(1−fair) は本調査が追加した診断値で、著者の測定した固体摩擦係数ではない。原著データと自作仮定を混同してフィットしない。

## Claudeの公開資料

[物性値照合_自律ループv2v3.md](../../調査台帳/物性値照合_自律ループv2v3.md)、[計算部品索引](../../調査台帳/計算部品索引.md)、[回覧板](../../回覧板.md)を確認。開始時の正本コミットは63aa160aafda955d66ffdf3b94bd7e5eb7028dce。

公開物性台帳のLF正規化SHA256は054c9388de3be3bd251c395059a9e02c9d3b336885236683ba3f528ff819d71f。前巡と同じ内容で、新たな物理実験やv3元コードの公開を確認したとは記載しない。

Claude台帳にある雪のHV・SfとMohr–Coulomb粘着力の区別、未照合の乾燥摩擦入力、計算内同時条件率と実験成功率の区別を継承する。今回の空気荷重分担率にも同じ区別を適用した。受領・返答・稼働状態は未確認。
