# 第30巡 出典台帳

確認日：2026-10-08。一次論文・公式物性式のみを根拠とする。著者の実測、著者の推算、本報告の仮定・計算を区別した。第三者の全文・図は研究成果として再配布しない。参照用に取得したPDF/XMLはGitHub保存照合後に作業フォルダとともに削除する。

| ID | 一次資料 | 今回確認した箇所 | 使用上の境界 |
|---|---|---|---|
| S1 | Hou et al., *A super liquid-repellent hierarchical porous membrane for enhanced membrane distillation*, Nature Communications 14, 6886 (2023), [DOI](https://doi.org/10.1038/s41467-023-42204-7), [出版社](https://www.nature.com/articles/s41467-023-42204-7), [全文XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10613234/fullTextXML) | Table 1のPE対照5行、接触角・液侵入圧のMethods。PDF p.3の表も画像で照合 | 塩水の侵入測定と外面の見掛け角。誤差幅は表記通り。シリコーン系被覆の性能を採用していない |
| S2 | *Mesoporous Membrane Materials Based on Ultra-High-Molecular-Weight Polyethylene: From Synthesis to Applied Aspects*, Membranes 11, 834 (2021), [DOI](https://doi.org/10.3390/membranes11110834), [全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC8624307/), [出版社PDF](https://mdpi-res.com/d_attachment/membranes/membranes-11-00834/article_deploy/membranes-11-00834-v2.pdf) | 多孔化・膜寸法保持、PDF p.14のYoung–Laplace推算 | 約250barは実測耐圧ではない。膜を低密度粒へ外挿しない |
| S3 | Tian et al., *Shortening the Saturation Time of PBAT Sheet Foaming via the Pre-Introducing of Microporous Structures*, Materials 18(5), 1044 (2025), [DOI](https://doi.org/10.3390/ma18051044), [全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC11901114/), [全文XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11901114/fullTextXML) | §§2.1–2.3、3.3–3.5。原樹脂密度、シート条件、前処理12hと後段2h、直接9h、前処理後密度 | 室温圧縮、工場での高圧発泡。工程量試算は材料占有容積のみ、容器設計や価格ではない |
| S4 | Meuchelböck et al., *Compression testing of EPP bead foams in a vacuum chamber: Experimental investigation on the influence of the cell gas*, Polymer Testing 132, 108388 (2024), [DOI](https://doi.org/10.1016/j.polymertesting.2024.108388), [著者大学の全文PDF](https://epub.uni-bayreuth.de/id/eprint/8347/2/1-s2.0-S0142941824000655-main.pdf) | §§2–4。EPP成形体、減圧条件、気体が変形・除荷回復へ及ぼす影響 | 今回の密閉セル式をこの実験の曲線にフィットしていない。粒床や50℃試験ではない |
| S5 | Morton et al., *Mechanical response of low density expanded polypropylene foams in compression and tension at different loading rates and temperatures*, Materials Today Communications 23, 100917 (2020), [DOI](https://doi.org/10.1016/j.mtcomm.2020.100917), [出版社索引ページ](https://doi.org/10.1016%2Fj.mtcomm.2020.100917) | 出版社公開の概要・温度依存部。Foam A、室温と60℃の崩壊応力比較 | 60℃の数値を50℃へ補間せず、粒化・長時間・湿潤の性能へ外挿しない。直接アクセスは403になる場合がある |
| S6 | IAPWS, *Revised Release on the Surface Tension of Ordinary Water Substance*, R1-76(2014), [公式ページ](https://iapws.org/technical-guidance/release/Surf-H2O), [公式PDF](https://iapws.org/relguide/Surf-H2O-2014.pdf) | 表面張力の相関式と適用温度域 | 純水と純水蒸気の平衡。塩水・汚染・界面活性物質入りには無修正で使わない |

## 入力の出所

- inputs.json の pe_observations：S1 Table 1の5行。diameterは公称値。侵入圧・後退角・履歴幅とその±幅を転記。角度からの侵入圧計算は本報告が意図的に行った未校正の短絡例。
- factory の source_S3_*：S3。それ以外の床厚・密度・面積・製造日数・時間・歩留まりは比較用仮定。
- 圧力履歴、直管径・角度、四喉部の配置、固体率、圧縮ひずみ、ポリトロープ指数：本報告の仮想例。実材料の同定値ではない。
- γ(T)：S6式。S1短絡例だけは比較条件として0.072N/mを固定した。塩水試験条件と揃えていないことを本文と図に明示。
- 物理実験0件。既存論文の試験を本計画の実証回数へ加算しない。

## 取得資料の照合記録

以下は今回取得した版のSHA-256。ファイル本体は本フォルダへ収録せず、再取得用URLは上表に示した。本文・図の抽出に失敗した箇所を実測値の根拠にしていない。

| 資料取得名 | bytes | SHA-256 |
|---|---:|---|
| membrane2023.xml | 214918 | 52e6d91107ef6471072b38f4dd0377a95a06d3bbf7d84932d71d9e7eed711424 |
| membrane2023.pdf | 2151081 | 50fd368d852b3e9aa556e75dc0ef6b72152cffe5ef506f2c3de46adaa4aa89aa |
| crazing2021.xml | 123232 | d1a3fa979b07292e45063eedef0a238b074ee1094fbe94bfcd291a3a2b2a3847 |
| crazing2021.pdf | 4436734 | 26d39f0987aa45ef82590f7824f340a2dea4b95a1bd45f5d09a1602f62032ed3 |
| pbat2025.xml | 154970 | 8cb2bc44fde05289bdb29f0afbb253002c59fc0d4ca6d614e9100d04dcafe6bb |
| gas2024.pdf | 2269312 | 5b4c832864f07db397858c5d5c1a40b7cd73702214309f5fa98254bebe951165 |
