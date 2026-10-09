# 第97巡の出典と適用範囲

確認日：2026-10-10。原論文・メーカー資料と、本巡の仮定を分ける。本文や原図・第三者PDFは転載しない。

| ID | 一次資料と確認範囲 | 本巡で使うもの／使わないもの |
|---|---|---|
| S1 | Martínez-Rubio et al. (2025), The complex crystalline behavior and tribological performance of polyhydroxyalkanoates, Polymer 340, 129207. [DOI](https://doi.org/10.1016/j.polymer.2025.129207)・[著者Pamiesが公開した受理稿](https://www.researchgate.net/publication/396572813_The_complex_crystalline_behavior_and_tribological_performance_of_polyhydroxyalkanoates) | 著者公開稿のHTML全文からMethods、Fig.5周辺、Table5–7を確認。Eの時間べき指数と密度を算術入力に使用。50℃物性・スキー摩擦・摩耗寿命へ転用しない |
| S2 | [CJ Biomaterials：PHACT A1000P公式製品ページ](https://cjbiomaterials.com/pha-sustainable-biopolymer/phact-a1000p/) | 非晶性の柔らかなPHA、密度1.23、他ポリマーの改質用途を確認。50℃×5hは乾燥条件で、50℃荷重使用の認証ではない。生分解認証も完成スキー材の無害性ではない |
| S3 | [Bluepha：BP350 TDS、2022-06-16改訂](https://www.bluepha-en.com/_files/ugd/935e6d_bcee95d4b23745ec9c44465b26fc2427.pdf) | 旧BP350のTm139℃、DTUL86℃（0.45MPa）、曲げ弾性率640MPa。BP350-05論文試料と同一仕様とは確認していない。これをE50へ代入しない |
| S4 | [Bluepha：2022年フィルム押出加工ガイド](https://www.bluepha-en.com/_files/ugd/935e6d_632a1d32d0574b94b96acc6a0724f18e.pdf) | 乾燥・溶融時の加水分解、加工後製品の湿気と日射を避けた50℃未満保管を確認。これは保管条件であり、50℃の屋外使用可否を決着する試験ではない |

S1の出版社検索本文で書誌・要旨を、Crossref APIでDOIを照合した。出版社直接取得は403、著者PDFの取得も403。本文は著者が公開した受理稿のHTML表示で読めた。最終版との全表の逐語照合・生測定データ再解析・PDFの図の数値化は未実施。正確な摩擦・DMA試験温度は入力をnullにした。Fig.5の指数に付された±値は感度の幅として使い、信頼区間や製品成功確率とは扱わない。

[公式ダウンロード一覧](https://www.bluepha-en.com/%E5%89%AF%E6%9C%AC-download-center)にはBP350-05の項目があるが、本巡で本文を取得したTDSはS3の旧BP350。品番・密度・温度条件の違いを埋めない。資料記載の剛性、熱たわみ、融点は異なる尺度である。

PHAの開放粒は[第37巡](../GPT回答_多方向探索第37巡_一括発泡による開放粒と雨後重量の設計_20261008.md)、分解と微粉流出は[第43巡](../GPT回答_多方向探索第43巡_微粉を流さない材料と雨水回収の設計_20261009.md)ですでに検討。PHA自体を新発見としない。Claudeの自律ループv2にもP3HB4HBの候補記載がある。本巡の追加は2025年の具体グレードの成形後変化と傷試験を照合し、出荷前調整と費用境界へ結び付けた点。

濡れたTPUの50℃摩耗の一次資料は[第59巡](../GPT回答_多方向探索第59巡_濡れた静摩擦を越える開離復帰と材料分担_20261009.md)既出。柔らかい材料を選ぶだけでは低摩擦・復帰にならないという比較条件を維持する。
