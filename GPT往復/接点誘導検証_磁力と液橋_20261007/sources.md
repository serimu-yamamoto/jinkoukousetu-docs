# 一次資料と使用範囲

閲覧日：2026-10-07。第三者の図・PDFは転載していない。文献の値と本研究の仮定を区別する。

| ID | 一次資料 | 今回使用した部分 | 転用しないもの |
|---|---|---|---|
| S1 | [Cox・Wang・Barés・Behringer / arXiv:1511.02219](https://arxiv.org/abs/1511.02219) | 粒の低荷重での組織化と締固め後の支持を分ける発想。本文・図2周辺を確認 | 2D円板の配合しきい値、測定力、摩擦、結晶秩序を本床へ移さない。PDFの表示日とarXiv識別子の年が異なるため最新版刊行年を推測しない |
| S2 | [Arnold Plastiform 2039公式資料](https://www.arnoldmagnetics.com/wp-content/uploads/2017/11/Plastiform-2039-Magnetic-Material-Datasheet.pdf) | Br・温度係数・密度を比較尺度に使用。Feb 2010 Rev. A | 70µm部品の保証、人体・環境安全、価格、J_eff=Brという同一視 |
| S3 | [Bagheri・Roy・Pöschel 2024 / DOI 10.1007/s40571-024-00772-5](https://link.springer.com/article/10.1007/s40571-024-00772-5) | 式24。接する同半径球・接触角0・V/R³=10⁻⁶〜10⁻¹の比較 | PEの接触角、未接触での捕捉、飽和床、雨と蒸発後の床強度 |
| S4 | [IAPWS Surface Tension of Ordinary Water Substance](https://iapws.org/technical-guidance/release/Surf-H2O) / [公式PDF](https://iapws.org/technical-guidance/release/Surf-H2O.download) | 純水の平衡表面張力式と50℃の表値67.94mN/m | 汚染水、実材料との動的ぬれ、摩擦係数 |
| S5 | [Kevin Zhou・Electromagnetism VIII Solutions](https://knzhou.github.io/handouts/E8Sol.pdf) | 問題10の磁気像法。式を独立実装 | 査読材料実験ではない。有限の尖った鋼製エッジの吸着や上限保証 |
| S6 | [第8巡の固定コミット](https://github.com/serimu-yamamoto/jinkoukousetu-docs/tree/9565960ab919415f20cdf2e29c73b8c0ff367c4a/GPT往復/接点検証_曲がるクリップの着脱_20261007) | 自作した非線形クリップの力経路。SHA-256で照合 | 実物の着脱測定、静止摩擦遷移、疲労、動的安定性 |

磁気双極子の力は固定モーメントの標準式を使い、エネルギーの距離微分と一致することを数値確認した。実部品が一様磁化された理想球と同じ挙動をするという実測資料は取得していない。
