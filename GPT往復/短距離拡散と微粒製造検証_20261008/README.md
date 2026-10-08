# 第31巡 再現資料：短距離拡散と微粒製造

[研究報告へ戻る](../GPT回答_多方向探索第31巡_短距離拡散と微粒製造を両立する設計_20261008.md)

| ファイル | 内容 |
|---|---|
| [inputs.json](inputs.json) | 一次資料の観察値、仮定、境界条件と未対応の物理 |
| [calculate.py](calculate.py) | 拡散の解析・差分解、粒数・皮重量・工程量と費用枠 |
| [results.json](results.json) | 15拡散、12脱離、36製粒、30外皮条件、差分照合等 |
| [validation.json](validation.json) | 25項目の数値照合。材料の合格試験ではない |
| [plot.py](plot.py) | 2図の再生成 |
| [figure1_diffusion_and_release.png](figure1_diffusion_and_release.png) | 小さい前駆体への拡散と脱離の比較 |
| [figure2_particle_count_and_skin.png](figure2_particle_count_and_skin.png) | 必要粒数と外皮重量の寸法依存 |
| [sources.md](sources.md) | 5一次資料の確認範囲・入力出所・取得版ハッシュ |
| [publication-manifest.json](publication-manifest.json) | 報告・再現資料・共有入口の保存照合用ハッシュ |

## 再計算

Python 3.10以降。計算本体は標準ライブラリのみ。図はmatplotlibを使用（作業版3.11.2）。生成JSONはUTF-8・LF。プロジェクト環境のRTKルールに従って次を実行する。

~~~text
python calculate.py
python plot.py
~~~

結果は本フォルダへ上書きする。指定した基準入力に対する参照照合も含むため、入力を変える場合は参照条件を確認する。Dや粒密度を有利に変えた計算を実証と数えない。

## 照合範囲

拡散の初期・長時間・単調性、逆算、寸法/D依存、掲載式の差、初期粒質量、脱離範囲、独立差分法の空間・時間分割、製粒の質量収支、面積・歩留まり・補充、外皮体積と密度定義を確認した。25/25は実物の成功率ではない。

sphereのRは発泡前半径、slabのLは半厚。finished_diameterは発泡後の球相当径。かさ密度・粒外形密度・樹脂実質密度を区別する。外皮模型は別の幾何感度で、製粒表の粒密度と同じ測定試料ではない。

physical_tests=0、physical_success_probability=null。装置・試料・購入価格の測定値を新たに取得した計算ではない。

## 保存

mainへ保存後、不変コミットのraw内容を全ファイル再取得し、ローカルとのバイト一致・SHA-256を検査。manifest自身も別途照合する。完了後はローカル研究コピー・Git履歴・参照PDF/XML・図生成依存を削除し、接続案内と既存設定を保持する。
