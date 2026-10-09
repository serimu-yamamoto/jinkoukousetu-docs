# 再利用する計算部品

- [slab_moisture_response.py](slab_moisture_response.py)：一定Dの両面平板吸湿・境界ステップ乾燥・寸法尺度を級数と有限体積で比較。膨張や現地50℃性能は予測しない。[第131巡](../GPT往復/吸湿平衡を基準にした細い粒の材料設計_20261010/README.md)。

- [linked_shrinkage_patches.py](linked_shrinkage_patches.py)：分割した収縮接点を有限ばねで連結し、端点縮約と全体有限要素で再拘束・荷重分流を比較。実氷や破壊を予測しない。[第130巡](../GPT往復/氷橋で連結された冬季接点の再評価_20261010/README.md)。

- [shrinkage_patches.py](shrinkage_patches.py)：収縮する局所接合帯と外部せん断荷重の伝達を解析式・一次元有限要素で比較。凍結耐久や成功率は予測しない。[第129巡](../GPT往復/凍結脱水と分割した冬季接点の拘束評価_20261010/README.md)。

- [formation_conditioning.py](formation_conditioning.py)：形成・後処理の物量時間、代表径による条件付き面積/個数合わせ、残留在庫を区別。安全・摩擦・採算は予測しない。[第128巡](../GPT往復/温暖粒形成と結晶安定化の工程分離_20261010/README.md)。

- [contact_rearrangement.py](contact_rearrangement.py)：粒間滑り・硬化の履歴と正味仕事の分配、有限時間回復の識別反例。雪感や材料成功率を予測しない。[第127巡](../GPT往復/雪の永久変形と粒接点の再配置設計_20261010/README.md)。

- [rolling_slip_audit.py](rolling_slip_audit.py)：回転数と径比から3種の滑り率・相対速度・接点仕事を監査。摩擦係数・温度・滑走感は予測しない。[第126巡](../GPT往復/高分子接点の乾湿摩擦と滑り率の定義監査_20261010/README.md)。

- [stop_hex.py](stop_hex.py)：円盤・段付き突起のHex8静的線形解析。既存要素を再利用し整合分布荷重と反力を診断。接触・実材50℃を予測しない。[第125巡](../GPT往復/短い粒内突起の三次元変形と根元補強_20261010/README.md)。

- [stop_misalignment.py](stop_misalignment.py)：円端面の位置ずれと名目荷重配分、片側・段付き突起の体積と理想梁成分。付着・短柱3D・滑走を予測しない。[第124巡](../GPT往復/粒内突起の位置ずれと片側受け面の比較_20261010/README.md)。

- [drying_stop_geometry.py](drying_stop_geometry.py)：乾湿の三方向形状比と対向突起の固体増加・名目荷重集中。力学、接着、滑走は予測しない。[第123巡](../GPT往復/乾湿で潰れない粒内ストッパーの成立条件_20261010/README.md)。

- [precipitation_bath_balance.py](precipitation_bath_balance.py)：析出原料と浴濃度、選択回収・抜出し・非溶剤補充の質量収支。形態・乾燥・滑走は予測しない。[第122巡](../GPT往復/液中形状形成と母液循環の濃度管理_20261010/README.md)。

- [compound_contact_inventory.py](compound_contact_inventory.py)：質量分率と理想体積分率、局所複合部物量、分散相寸法、同試験内の報告値比。寿命予測ではない。[第121巡](../GPT往復/高温乾式PK複合材の実施例と局所配合設計_20261010/README.md)。

- [material_beam_screen.py](material_beam_screen.py)：等曲げ剛性の厚さ・質量・応力と、局所置換原料費・交換寿命の境界。材料入力は未較正。[第120巡](../GPT往復/耐摩耗候補と枝の柔らかさを両立する材料選定_20261010/README.md)。

- [clump_surface_cycle.py](clump_surface_cycle.py)：球列の接触包絡と符号付き周期仕事、解析平均、ピーク解像度。実物摩擦・DEM全体の予測ではない。[第119巡](../GPT往復/球列近似の凹凸と接触仕事の監査_20261010/README.md)。

- [boundary_pressure.py](boundary_pressure.py)：名目圧力と局所圧力の識別反例、側壁力の圧力換算、自重尺度。実物の粘着力を推定しない。[第118巡](../GPT往復/境界力と見かけの粘着力の識別_20261010/README.md)。

- [vibration_dwell.py](vibration_dwell.py)：振幅/粒径と加速度比の相似、局所滞留と全閉鎖の時間収支。絡み形成・雪の性能は予測しない。[第117巡](../GPT往復/粒の絡みと振動整地の時間尺度_20261010/README.md)。

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
