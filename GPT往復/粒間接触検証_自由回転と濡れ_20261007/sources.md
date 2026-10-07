# 出典と適用範囲

確認日：2026-10-07。

| 資料 | 使用した内容 | 使用しない外挿 |
|---|---|---|
| [Modern Robotics 12.2.1 Friction](https://modernrobotics.northwestern.edu/nu-gm-book-resource/12-2-1-friction/)、著者公式教材 | 圧縮反力、摩擦円錐、接触点によるモーメントの枠組み | 材料・人工雪・粒床の実測結果ではない |
| [IAPWS R1-76(2014)](https://iapws.org/documents/release/Surf-H2O.download)、p.3式・p.4表 | 純水の気液平衡の表面張力式と50℃の照合値 | 樹脂の接触角、実液橋の存在、汚れた水の物性は与えない |
| [Bocquetほか、C. R. Physique 3 (2002) 207–215](https://comptes-rendus.academie-sciences.fr/physique/item/10.1016/S1631-0705(02)01312-9.pdf) | 球接触の液橋力尺度、粗さ・荷重履歴の影響 | 今回の交差線材・樹脂・液量の実測へ直接転用しない |
| [Kim, Wu, Han (2025), Percolation transition in entangled granular networks](https://www.nature.com/articles/s41467-025-66228-3) | C形粒の幾何接続と力学的保持の区別 | 鋼・mm寸法の振動条件、時間、結合の割合を微細樹脂粒や雪感へ移さない |
| [第12巡](../GPT回答_多方向探索第12巡_接触の偏りと自整列の成立条件_20261007.md)、commit 6af4fb7 | R4形状、単粒重心と自重の仮定、固定端問題からの継続 | 独立外部実証ではない |
| [第11巡](../GPT回答_多方向探索第11巡_閉じた補強輪による支持と局所変形の分離_20261007.md) | 材料密度・粒数・税別費用の比較基準 | 実見積りや量産歩留まりとして扱わない |

接触高さの区間被覆、円弧形状C3、指定配置の数値計算、面の内外分類、費用換算は今回の独自検討。資料の存在や数式検証を、人の滑走、50℃耐久、人体安全、成功率90%超の実証にしない。
