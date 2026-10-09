# 再利用する計算部品

- [platelet_exposure.py](platelet_exposure.py)：板の回転・突出・被覆・寸法区間と定常再加工収支。幾何露出を摩擦や接触面積に換算しない。[第116巡](../GPT往復/結晶足場と露出保持の幾何条件_20261010/README.md)。

- [enzyme_crystal_process.py](enzyme_crystal_process.py)：中性酵素反応の物量、リン原子収支、分離/配置損失、実験投入比の換算。酵素能力・形態・滑走を予測しない。[第115巡](../GPT往復/中性結晶化の工程負担と雨後相変化_20261010/README.md)。

- [crystal_platelet_inventory.py](crystal_platelet_inventory.py)：板全厚による体積換算、配置歩留まりと晶析歩留まりを分離した仕込み量。形成・摩擦・安全の実物検証ではない。[第114巡](../GPT往復/生体分子結晶の接触相と製造物量_20261010/README.md)。

- [response_identifiability.py](response_identifiability.py)：単一複素測定に一致するSLS族、支持の幾何補償、局所質量費。第112巡の数学式を再利用し、高周波の実材妥当性は未証明。[第113巡](../GPT往復/実測動的物性と高周波推定の識別_20261010/README.md)。

- [viscoelastic_glide.py](viscoelastic_glide.py)：指定正弦変形のSLS応答、周期仕事、同じ動的硬さの比較、独立時間積分。実材パラメータ未同定。[第112巡](../GPT往復/滑走速度と接触変形の時間尺度_20261010/README.md)。

- [washing_selectivity.py](washing_selectivity.py)：結晶精製の選択性・水量・損失補充費。[第111巡](../GPT往復/結晶精製の選択性と洗浄順序_20261010/README.md)。製品残留・装置性能は未測定。

- [powder_inventory.py](powder_inventory.py)：結晶接触材の粒度・局所量・補充費。[第110巡](../GPT往復/結晶接触材の粒度基準と保持量監査_20261010/README.md)。保持・摩擦・捕集率は未測定。

- [contact_fabric.py](contact_fabric.py)：接点配向と自由回転を含む微小支持模型。[第109巡](../GPT往復/接点配向と回転を含む支持解放の比較_20261010/README.md)。大変位解放・50℃・実床は未実証。

- [load_unload_foundation.py](load_unload_foundation.py)：移動する押込み履歴の変形仕事と同深さ比較。[第108巡](../GPT往復/滑走方向の変形仕事と横解放の分離_20261010/README.md)。横切削・50℃材料未同定。

- [restoration_process.py](restoration_process.py)：保持水切りと分流復旧の収支。[第107巡](../GPT往復/分流水切りと60分復旧の成立条件_20261010/README.md)。実機能力・実物損傷未検証。

- [rim_grain_hex.py](rim_grain_hex.py)：環粒のHex8弾性と開口の毛管圧尺度。[第106巡](../GPT往復/開放環粒の三次元支持と毛管残水の比較_20261010/README.md)。大窓メッシュ未収束。

- [formation_routes.py](formation_routes.py)：環粒の幾何、乾燥・延べ加工・原料回収の収支。[第105巡](../GPT往復/温暖形成と開放環粒の製造監査_20261010/README.md)。

- [flared_ligament.py](flared_ligament.py)：可変幅支柱のQ4平面応力、断面と局所流路の積分。[第104巡](../GPT往復/拡大流路と支持剛性の連成監査_20261010/README.md)。

- [graded_contact.py](graded_contact.py)：区分一次剛性と自由回転の片側接触。handover_contacts.pyの幾何を再利用。[第103巡](../GPT往復/受け面の剛性勾配と薄枝実現条件の検証_20261010/README.md)。

- [handover_contacts.py](handover_contacts.py)：第102巡の圧縮のみの局所接触・重なり面積・曲面受渡し。標準ライブラリのみ。50℃や実粒の物性は未較正。
- [入力・再現・限界](../GPT往復/曲面補償と面積受渡しの有限形状検証_20261010/README.md)。正本はこのGitHub。サーバーの ~/firn/lib へ展開して利用できる。今回の作業用コピーは公開照合後に削除する。
