# 出典と利用範囲

閲覧日：2026-10-07。原文を大量転載せず、参照位置とこの研究で使う範囲を記録する。

1. [Celanese, Hostaform POM Product Manual](https://www.celanese.com/-/media/Engineered%20Materials/Files/Product%20Sell%20Sheets/POM-062_HostaformProductManual_EU_EN_0614.pdf)。PDF38ページ Fig.08、C9021の曲げクリープ弾性率、20/50/80/100℃、外側曲げ応力10MPa。時間・温度・応力の一致が必要なことの一次資料。50℃・4時間値は本巡では採取していない。耐熱表示や無負荷の熱老化を、荷重下のクリープ弾性率へ代用しない。強化材・滑剤入りグレードは採用していない。
2. [Grünewald, Sumpf, Golder, Oscillating tribological long-term investigations of PTFE and microcapsule filled POM](https://link.springer.com/article/10.1007/s44493-025-00004-z), DOI 10.1007/s44493-025-00004-z、2025-12-01公開。Materials、Tribometry、Friction and wear against UHMWPEを参照。無充填対照を含む材料対の摩擦が、時間と試験条件で変わることを利用。0.25m/sの板状試験を80m/s・50℃・粒床に移さない。配合群の摩擦範囲を特定材料の厳密な終値にしない。論文の油入りマイクロカプセル・PTFEは本案に使用しない。
3. [第13巡の接触・力・費用データ](../粒間接触検証_自由回転と濡れ_20261007/README.md)、参照コミット ad65e22a7691ecd6bf9049ef1f2894a935a49cb6。cluster_results.json、wet_cost_results.jsonが今回の直接入力。資料中の仮定を実測に格上げしない。
4. [第12巡の骨格モデル](../接触配分検証_傾きと自整列_20261007/README.md)、参照コミット 6af4fb724a1331265309447d4b913de1b13e86c4。曲線部材のエネルギー積分を一般化し、自由粒と表面荷重へ変更した。今回は表面接触の腕の長さを局所偶力に含めている。
5. [第3巡の材料比較](../GPT回答_多方向探索第3巡_材料の摩擦と50℃耐久を分ける設計_20261007.md)。低密度材の費用と別材の剛性を無条件に合成しないという既存課題へ接続。

新しい梁式、支柱/斜材の設計、被覆距離評価、数値比較、予算条件は本研究内の計算。現物測定値、見積書、特許調査結果ではない。
