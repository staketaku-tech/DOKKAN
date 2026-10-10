import streamlit as st
import math
import pandas as pd
from damage_core import calculate_dokkan_def, calculate_damage, max_enemy_atk, reverse_enemy_atk
from practical_ui import render_practical_tab

# --- セッション情報の初期化 ---
if "def_results" not in st.session_state:
    st.session_state.def_results = []

# --- 各種データ定義 ---
POTENTIAL_DEF_DATA = {
    "高成長 (速)": [2000, 4100, 4400, 4500, 5400],
    "標準成長 (技・知)": [2000, 3700, 4000, 4100, 5000],
    "低成長 (力・体)": [2000, 3300, 3600, 3700, 4600],
}
POTENTIAL_ATK_DATA = {
    "高成長 (力・技)": [2000, 4100, 4400, 4500, 5400],
    "標準成長 (速・知・体)": [2000, 3700, 4000, 4100, 5000],
}
ULTRA_KI_MULTI_OPTIONS = {
    "0倍 (URキャラ用)": 0, "1.4倍 (通常、イベ産)": 140, "1.5倍 (フェスUR等)": 150, 
    "1.6倍 (高倍率LR通常等)": 160, "2.0倍 (LR最大)": 200
}
NORMAL_KI_MULTI_OPTIONS = {
    "1.4倍 (通常、イベ産)": 140, "1.5倍 (フェスUR等)": 150, 
    "1.6倍 (高倍率LR通常等)": 160, "2.0倍 (LR最大)": 200
}
SA_BASE_OPTIONS = {
    "極大Lv20 (4.25倍)": 425, "極大Lv25 (4.5倍)": 450, "超絶特大Lv10 (5.05倍)": 505, 
    "超極大Lv20 (5.7倍)": 570, "超極大Lv25 (6.2倍)": 620, "超絶特大Lv15 (6.3倍)": 630, "究極Lv20 (8.4倍)": 840
}
DURATIONS = {"1ターン (そのターンのみ)": 1, "3ターン (次登場まで持続)": 3, "4ターン (次登場まで持続)": 4, "無限上昇 (99ターン)": 99}
ACTIVE_BASE_OPTIONS = {"無し (攻撃無し)": 0, "超極大 (4.25倍)": 425, "究極 (5.5倍)": 550, "究極 (6.0倍/特殊)": 600}

def get_def_growth_type(element_str):
    if "速" in element_str: return "高成長 (速)"
    elif "技" in element_str or "知" in element_str: return "標準成長 (技・知)"
    else: return "低成長 (力・体)"

def get_atk_growth_type(element_str):
    if "力" in element_str or "技" in element_str: return "高成長 (力・技)"
    else: return "標準成長 (速・知・体)"


def calculate_dokkan_atk(base, ls, supp_mem, add_p, field, active, link, ki_multi, mult_p, sa_total_multi):
    val = math.floor(base * (1 + ls / 100))
    val = math.floor(val * (1 + supp_mem / 100))
    val = math.floor(val * (1 + add_p / 100))
    val = math.floor(val * (1 + field / 100))
    val = math.floor(val * (1 + link / 100))
    val = math.floor(val * (1 + active / 100))
    val = math.floor(val * (ki_multi / 100))
    val = math.floor(val * (1 + mult_p / 100))
    val = math.floor(val * (sa_total_multi / 100))
    return val

def calculate_dokkan_active_atk(base, ls, supp_mem_field_add, link, active_self_buff, max_ki_multi, mult_p_normal, mult_p_sa_on, active_total_multi):
    val = math.floor(base * (1 + ls / 100))
    val = math.floor(val * (1 + supp_mem_field_add / 100))
    val = math.floor(val * (1 + link / 100))
    val = math.floor(val * (1 + active_self_buff / 100))
    val = math.floor(val * (max_ki_multi / 100))
    val = math.floor(val * (1 + mult_p_normal / 100))
    val = math.floor(val * (1 + mult_p_sa_on / 100))
    val = math.floor(val * (active_total_multi / 100))
    return val

# ==========================================
# WebアプリのUI構築
# ==========================================
st.set_page_config(page_title="ドッカンバトル 総合計算ツール", layout="wide", initial_sidebar_state="collapsed")
st.title("🐉 ドッカンバトル 総合計算ツール")

tab1, tab2, tab3, tab4 = st.tabs([
    "🛡️ DEFシミュレーター", 
    "⚔️ ATKシミュレーター", 
    "📱 実戦ダメ計 (即席)", 
    "🔍 敵ATK逆算"
])

# ==========================================
# タブ1: DEF & 被ダメージ
# ==========================================
with tab1:
    st.markdown("### 👤 キャラクター設定")
    col1, col2 = st.columns(2)
    with col1:
        st.caption("■ 基礎ステータス")
        col_st1, col_st2, col_st3 = st.columns(3)
        with col_st1: raw_def = st.number_input("素のDEF", min_value=0, value=8000, step=100, key="d_raw")
        with col_st2: element_def = st.selectbox("属性 (クラス)", options=["超速", "極速", "超技", "極技", "超知", "極知", "超力", "極力", "超体", "極体"], key="d_elem")
        with col_st3: dupe_level_def = st.selectbox("凸数 (DEF)", options=["0凸 (55%)", "1凸 (右下解放)", "2凸 (左上解放)", "3凸 (右上解放)", "4凸 (虹)"], key="d_dupe")
        
        def_growth = get_def_growth_type(element_def)
        dupe_idx = ["0凸 (55%)", "1凸 (右下解放)", "2凸 (左上解放)", "3凸 (右上解放)", "4凸 (虹)"].index(dupe_level_def)
        hidden_def = POTENTIAL_DEF_DATA[def_growth][dupe_idx]
        skill_orb_def = st.number_input("スキル玉の合計DEF", value=0, step=100, key="d_orb")
        
        base_def = raw_def + hidden_def + skill_orb_def
        st.success(f"**最終的な基礎DEF: {base_def:,}** (潜在: +{hidden_def})")

    with col2:
        st.caption("■ 倍率パッシブ・リンク")
        col_pa1, col_pa2 = st.columns([1, 2])
        with col_pa1:
            def_ls = st.number_input("リーダースキル(%)", min_value=0, value=440, step=10, key="d_ls")
            def_link = st.number_input("リンクスキル(%)", min_value=0, value=25, step=5, key="d_link")
        with col_pa2:
            st.write("足し算パッシブ (%)")
            ca1, ca2, ca3 = st.columns(3)
            with ca1: d_add1 = st.number_input("①", value=150, step=10, key="d_a1", label_visibility="collapsed")
            with ca2: d_add2 = st.number_input("②", value=50, step=10, key="d_a2", label_visibility="collapsed")
            with ca3: d_adds = st.number_input("サポ", value=0, step=10, key="d_as", label_visibility="collapsed")
            def_add = d_add1 + d_add2 + d_adds
            
            st.write("掛け算パッシブ (%)")
            cm1, cm2, cm3 = st.columns(3)
            with cm1: d_mult1 = st.number_input("①", value=100, step=10, key="d_m1", label_visibility="collapsed")
            with cm2: d_mult2 = st.number_input("②", value=0, step=10, key="d_m2", label_visibility="collapsed")
            with cm3: d_mults = st.number_input("サポ", value=0, step=10, key="d_ms", label_visibility="collapsed")
            def_mult = d_mult1 + d_mult2 + d_mults

    st.markdown("---")
    st.markdown("### 🔥 必殺技と防御性能")
    col3, col4 = st.columns(2)
    with col3:
        st.caption("■ 必殺技の重ね掛け効果")
        c_sa1, c_sa2, c_sa3 = st.columns(3)
        with c_sa1:
            st.write("【超必殺技】")
            def_ultra_sa = st.number_input("DEF上昇(%)", min_value=0, value=50, step=10, key="d_usa")
            def_ultra_dur_k = st.selectbox("持続ターン", options=list(DURATIONS.keys()), index=3, key="d_udur", label_visibility="collapsed")
            def_ultra_pt = st.slider("1ターンの回数", min_value=0, max_value=10, value=1, key="d_upt")
            def_ultra_dur = DURATIONS[def_ultra_dur_k]
        with c_sa2:
            st.write("【通常必殺技】")
            def_normal_sa = st.number_input("DEF上昇(%) ", min_value=0, value=30, step=10, key="d_nsa")
            def_normal_dur_k = st.selectbox("持続ターン ", options=list(DURATIONS.keys()), index=3, key="d_ndur", label_visibility="collapsed")
            def_normal_pt = st.slider("1ターンの回数 ", min_value=0, max_value=10, value=1, key="d_npt")
            def_normal_dur = DURATIONS[def_normal_dur_k]
        with c_sa3:
            st.write("【EX必殺技】")
            def_ex_sa = st.number_input("DEF上昇(%)  ", min_value=0, value=50, step=10, key="d_esa")
            def_ex_dur_k = st.selectbox("持続ターン  ", options=list(DURATIONS.keys()), index=3, key="d_edur", label_visibility="collapsed")
            def_ex_pt = st.slider("1ターンの回数  ", min_value=0, max_value=10, value=0, key="d_ept")
            def_ex_dur = DURATIONS[def_ex_dur_k]

    with col4:
        st.caption("■ 軽減・ガード・特殊補正")
        guard_active = st.checkbox("🛡️ 全属性ガード発動", value=False, key="d_guard")
        c_dr1, c_dr2 = st.columns(2)
        with c_dr1: dmg_reduction_before = st.number_input("軽減率【行動前】(%)", min_value=0, max_value=100, value=0, step=10, key="d_dr_b")
        with c_dr2: dmg_reduction_after = st.number_input("軽減率【行動後】(%)", min_value=0, max_value=100, value=0, step=10, key="d_dr_a")
        
        with st.expander("✨ 特殊補正 (メモリー/フィールド等)"):
            c_sp1, c_sp2, c_sp3 = st.columns(3)
            with c_sp1: def_mem = st.number_input("メモリー(%)", min_value=0, value=0, step=1, key="d_mem")
            with c_sp2: def_field = st.number_input("フィールド(%)", min_value=0, value=0, step=1, key="d_field")
            with c_sp3: def_act = st.number_input("アクティブ(%)", min_value=0, value=0, step=10, key="d_act")

    st.markdown("---")
    st.markdown("### 👹 敵の攻撃とシミュレーション実行")
    col5, col6, col7, col8 = st.columns(4)
    with col5: enemy_atk_man = st.number_input("敵必殺ATK (万)", min_value=0, value=150, step=10, key="d_eatk")
    with col6: enemy_class = st.selectbox("敵クラス", options=["超系", "極系"], index=1, key="d_eclass")
    with col7: enemy_element = st.selectbox("属性相性", options=["有利", "等倍", "不利"], index=1, key="d_eelem")
    with col8: survival_dmg_man = st.number_input("耐久ライン (万)", min_value=0, value=80, step=10, key="d_surv")
    
    # ★ 敵の会心設定を追加
    with st.expander("💥 敵の特殊行動 (会心) 設定"):
        crit_active = st.checkbox("敵が会心を発動する", value=False, key="d_ecrit")
        c_ec1, c_ec2 = st.columns(2)
        with c_ec1: ecrit_atk_up = st.number_input("敵のATKアップ(%)", min_value=0, value=50, step=10, key="d_ec_atk")
        with c_ec2: ecrit_def_down = st.number_input("こちらのDEFダウン(%)", min_value=0, max_value=100, value=50, step=10, key="d_ec_def")

    enemy_atk = enemy_atk_man * 10000
    survival_dmg = survival_dmg_man * 10000

    if st.button("DEF推移と被ダメージを計算", type="primary", use_container_width=True, key="btn_def"):
        user_class = element_def[0]
        is_same_class = (user_class == enemy_class[0])
        
        if enemy_element == "有利":
            base_multi = 0.9 if is_same_class else 1.0
        elif enemy_element == "等倍":
            base_multi = 1.0 if is_same_class else 1.15
        else:
            base_multi = 1.25 if is_same_class else 1.5

        def calc_max_tolerable_atk(defense, dr, limit):
            return max_enemy_atk(defense, dr, limit, type_multi=base_multi, guard=guard_active, advantageous=enemy_element == "有利", crit=crit_active, crit_atk=ecrit_atk_up, crit_def=ecrit_def_down)

        st.info("計算順序：敵ATK × 属性補正（全属性ガード時は0.8）× 軽減 → DEFを引く → ガード時は0.5。表示値は乱数を含まない参考値です。")

        buff_queue_def = []
        results_def = []
        
        # 行動前の処理
        val0 = calculate_dokkan_def(base_def, def_ls, def_mem, def_add, def_field, def_act, def_mult, def_link, 0)
        
        dmg0 = calculate_damage(val0, enemy_atk, dmg_reduction_before, type_multi=base_multi, guard=guard_active, advantageous=enemy_element == "有利", crit=crit_active, crit_atk=ecrit_atk_up, crit_def=ecrit_def_down)
        
        results_def.append({
            "顔出し回数": "0. 行動前(先制)", 
            "DEF": val0, 
            "被ダメージ": dmg0,
            "完封可能 敵ATK": calc_max_tolerable_atk(val0, dmg_reduction_before, 0),
            f"耐久可能 敵ATK({survival_dmg_man}万)": calc_max_tolerable_atk(val0, dmg_reduction_before, survival_dmg)
        })

        for i in range(1, 10):
            turn_game = 2 * i - 1
            active_buffs = sum(effect for t_applied, dur, effect in buff_queue_def if turn_game < t_applied + dur)
            
            total_effect_this_turn = 0
            for _ in range(def_ex_pt):
                total_effect_this_turn += def_ex_sa
                buff_queue_def.append((turn_game, def_ex_dur, def_ex_sa))
            for _ in range(def_ultra_pt):
                total_effect_this_turn += def_ultra_sa
                buff_queue_def.append((turn_game, def_ultra_dur, def_ultra_sa))
            for _ in range(def_normal_pt):
                total_effect_this_turn += def_normal_sa
                buff_queue_def.append((turn_game, def_normal_dur, def_normal_sa))
                
            val = calculate_dokkan_def(base_def, def_ls, def_mem, def_add, def_field, def_act, def_mult, def_link, active_buffs + total_effect_this_turn)
            
            # ★ 敵会心の補正を適用
            
            dmg = calculate_damage(val, enemy_atk, dmg_reduction_after, type_multi=base_multi, guard=guard_active, advantageous=enemy_element == "有利", crit=crit_active, crit_atk=ecrit_atk_up, crit_def=ecrit_def_down)
            
            results_def.append({
                "顔出し回数": f"{i}. 登場{i}回目(行動後)", 
                "DEF": val, 
                "被ダメージ": dmg,
                "完封可能 敵ATK": calc_max_tolerable_atk(val, dmg_reduction_after, 0),
                f"耐久可能 敵ATK({survival_dmg_man}万)": calc_max_tolerable_atk(val, dmg_reduction_after, survival_dmg)
            })
        
        st.session_state.def_results = results_def
        st.session_state.last_enemy_class = enemy_class
        st.session_state.last_enemy_element = enemy_element
        st.session_state.last_guard = guard_active
        st.session_state.last_user_class = element_def
        
        df_def = pd.DataFrame(results_def).set_index("顔出し回数")
        
        st.success(
            f"🎯 **最終結果 (登場9回目)**\n\n"
            f"行動後DEF: **{results_def[-1]['DEF']:,}** ｜ "
            f"受けられる最大の敵ATK: (完封) **{results_def[-1]['完封可能 敵ATK']:,}** / "
            f"(耐久) **{results_def[-1][f'耐久可能 敵ATK({survival_dmg_man}万)']:,}**"
        )
        
        r1, r2 = st.columns([1, 2])
        with r1: 
            st.write("【DEFと被ダメージの推移グラフ】")
            st.caption("被ダメージ0はゲーム内の2桁ダメージ相当です。")
            st.line_chart(df_def[["DEF", "被ダメージ"]])
        with r2: 
            st.write("【詳細数値】")
            formatter = {
                "DEF": "{:,}",
                "被ダメージ": "{:,}",
                "完封可能 敵ATK": lambda x: f"{x:,}" if isinstance(x, int) else x,
                f"耐久可能 敵ATK({survival_dmg_man}万)": lambda x: f"{x:,}" if isinstance(x, int) else x
            }
            st.dataframe(df_def.style.format(formatter))

# ==========================================
# タブ2: ATK (表示火力) - 変更なし
# ==========================================
with tab2:
    st.markdown("### 👤 キャラクター設定")
    colA, colB = st.columns(2)
    with colA:
        st.caption("■ 基礎ステータス")
        ca_st1, ca_st2, ca_st3 = st.columns(3)
        with ca_st1: raw_atk = st.number_input("素のATK", min_value=0, value=12000, step=100, key="a_raw")
        with ca_st2: element_atk = st.selectbox("属性 (ATK)", options=["超速", "極速", "超技", "極技", "超知", "極知", "超力", "極力", "超体", "極体"], key="a_elem")
        with ca_st3: dupe_level_atk = st.selectbox("凸数 (ATK)", options=["0凸 (55%)", "1凸 (右下解放)", "2凸 (左上解放)", "3凸 (右上解放)", "4凸 (虹)"], key="a_dupe")
        
        atk_growth = get_atk_growth_type(element_atk)
        dupe_idx_atk = ["0凸 (55%)", "1凸 (右下解放)", "2凸 (左上解放)", "3凸 (右上解放)", "4凸 (虹)"].index(dupe_level_atk)
        hidden_atk = POTENTIAL_ATK_DATA[atk_growth][dupe_idx_atk]
        skill_orb_atk = st.number_input("スキル玉合計ATK", value=0, step=100, key="a_orb")
        
        base_atk = raw_atk + hidden_atk + skill_orb_atk
        st.success(f"**最終的な基礎ATK: {base_atk:,}** (潜在: +{hidden_atk})")

    with colB:
        st.caption("■ 倍率パッシブ・リンク")
        ca_pa1, ca_pa2 = st.columns([1, 2])
        with ca_pa1:
            atk_ls = st.number_input("リーダースキル(%)", min_value=0, value=440, step=10, key="a_ls")
            atk_link = st.number_input("リンクスキル(%)", min_value=0, value=50, step=5, key="a_link")
        with ca_pa2:
            st.write("足し算パッシブ (%)")
            aa1, aa2, aa3 = st.columns(3)
            with aa1: a_add1 = st.number_input("①", value=150, step=10, key="a_a1", label_visibility="collapsed")
            with aa2: a_add2 = st.number_input("②", value=50, step=10, key="a_a2", label_visibility="collapsed")
            with aa3: a_adds = st.number_input("サポ", value=0, step=10, key="a_as", label_visibility="collapsed")
            atk_add = a_add1 + a_add2 + a_adds
            
            st.write("掛け算パッシブ (%)")
            am1, am2, am3 = st.columns(3)
            with am1: a_mult1 = st.number_input("①", value=100, step=10, key="a_m1", label_visibility="collapsed")
            with am2: a_mult2 = st.number_input("②", value=0, step=10, key="a_m2", label_visibility="collapsed")
            with am3: a_mults = st.number_input("サポ", value=0, step=10, key="a_ms", label_visibility="collapsed")
            atk_mult = a_mult1 + a_mult2 + a_mults

    st.markdown("---")
    st.markdown("### 🔥 攻撃・必殺技設定")
    colC, colD = st.columns(2)
    with colC:
        st.caption("■ 必殺技の重ね掛け効果")
        ca_sa1, ca_sa2, ca_sa3 = st.columns(3)
        with ca_sa1:
            st.write("【超必殺技】")
            atk_ultra_base_k = st.selectbox("基本倍率", options=list(SA_BASE_OPTIONS.keys()), index=3, key="a_ubase", label_visibility="collapsed")
            atk_ultra_sa = st.number_input("ATK上昇(%)", min_value=0, value=50, step=10, key="a_usa")
            atk_ultra_dur_k = st.selectbox("持続ターン", options=list(DURATIONS.keys()), index=3, key="a_udur", label_visibility="collapsed")
            atk_ultra_pt = st.slider("1ターンの回数", min_value=0, max_value=10, value=1, key="a_upt")
            atk_ultra_base, atk_ultra_dur = SA_BASE_OPTIONS[atk_ultra_base_k], DURATIONS[atk_ultra_dur_k]
            
        with ca_sa2:
            st.write("【通常必殺技】")
            atk_normal_base_k = st.selectbox("基本倍率 ", options=list(SA_BASE_OPTIONS.keys()), index=2, key="a_nbase", label_visibility="collapsed")
            atk_normal_sa = st.number_input("ATK上昇(%) ", min_value=0, value=30, step=10, key="a_nsa")
            atk_normal_dur_k = st.selectbox("持続ターン ", options=list(DURATIONS.keys()), index=3, key="a_ndur", label_visibility="collapsed")
            atk_normal_pt = st.slider("1ターンの回数 ", min_value=0, max_value=10, value=1, key="a_npt")
            atk_normal_base, atk_normal_dur = SA_BASE_OPTIONS[atk_normal_base_k], DURATIONS[atk_normal_dur_k]
            
        with ca_sa3:
            st.write("【EX必殺技】")
            atk_ex_base_k = st.selectbox("基本倍率  ", options=list(SA_BASE_OPTIONS.keys()), index=6, key="a_ebase", label_visibility="collapsed")
            atk_ex_sa = st.number_input("ATK上昇(%)  ", min_value=0, value=50, step=10, key="a_esa")
            atk_ex_dur_k = st.selectbox("持続ターン  ", options=list(DURATIONS.keys()), index=3, key="a_edur", label_visibility="collapsed")
            atk_ex_pt = st.slider("1ターンの回数  ", min_value=0, max_value=10, value=0, key="a_ept")
            atk_ex_base, atk_ex_dur = SA_BASE_OPTIONS[atk_ex_base_k], DURATIONS[atk_ex_dur_k]

    with colD:
        st.caption("■ 気力ボーナスとその他の火力補正")
        c_ki1, c_ki2 = st.columns(2)
        with c_ki1:
            u_ki_choice = st.selectbox("気力ボーナス (超/EX必殺用)", options=list(ULTRA_KI_MULTI_OPTIONS.keys()), index=4, key="a_uki")
            ultra_ki_multi = ULTRA_KI_MULTI_OPTIONS[u_ki_choice]
        with c_ki2:
            n_ki_choice = st.selectbox("気力ボーナス (通常必殺用)", options=list(NORMAL_KI_MULTI_OPTIONS.keys()), index=1, key="a_nki")
            normal_ki_multi = NORMAL_KI_MULTI_OPTIONS[n_ki_choice]
            
        sa_potential_lv = st.number_input("潜在「必殺威力UP」Lv", min_value=0, value=0, max_value=30, step=1, key="a_plv")
        atk_turns = st.number_input("登場回数 (シミュレーション)", min_value=1, value=5, step=1, key="a_turns")
        
        with st.expander("✨ 特殊補正 (メモリー/フィールド/通常アクティブバフ)"):
            ca_sp1, ca_sp2, ca_sp3 = st.columns(3)
            with ca_sp1: atk_mem = st.number_input("メモリー(%)", min_value=0, value=0, step=1, key="a_mem")
            with ca_sp2: atk_field = st.number_input("フィールド(%)", min_value=0, value=0, step=1, key="a_field")
            with ca_sp3: atk_act = st.number_input("アクティブバフ(%)", min_value=0, value=0, step=10, key="a_act")

    with st.expander("☄️ 【攻撃系】アクティブスキル設定"):
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            active_choice = st.selectbox("アクティブのダメージ倍率", options=list(ACTIVE_BASE_OPTIONS.keys()), index=0)
            active_base = ACTIVE_BASE_OPTIONS[active_choice]
            active_self_buff = st.number_input("アクティブ発動時の一時バフ(%)", min_value=0, value=100, step=10)
        with col_act2:
            atk_mult_sa_on = st.number_input("必殺技発動時の掛け算パッシブ(%)", min_value=0, value=0, step=10)
            active_turn = st.slider("アクティブを撃つ登場回数", min_value=1, max_value=int(atk_turns), value=1)

    if st.button("ATK推移をシミュレーション", type="primary", use_container_width=True, key="btn_atk"):
        buff_queue_atk = []
        results_atk = []
        
        active_ki_multi = ultra_ki_multi if ultra_ki_multi > 0 else normal_ki_multi

        for i in range(1, atk_turns + 1):
            turn_game = 2 * i - 1
            active_buffs = sum(effect for t_applied, dur, effect in buff_queue_atk if turn_game < t_applied + dur)
            current_buff_accumulator = active_buffs
            
            ultra_atk_val, normal_atk_val, ex_atk_val, active_atk_val = 0, 0, 0, 0
            
            if i == active_turn and active_base > 0:
                total_active_multi = active_base + (sa_potential_lv * 5) + current_buff_accumulator
                atk_add_for_active = atk_add - atk_act
                
                active_atk_val = calculate_dokkan_active_atk(
                    base_atk, atk_ls, atk_add_for_active, atk_link, active_self_buff, 
                    active_ki_multi, atk_mult, atk_mult_sa_on, total_active_multi
                )
                if atk_mult_sa_on > 0:
                    atk_mult += atk_mult_sa_on

            ex_ki_multi_to_use = ultra_ki_multi if ultra_ki_multi > 0 else normal_ki_multi
            for e in range(atk_ex_pt):
                if e == 0:
                    total_multi = atk_ex_base + (sa_potential_lv * 5) + current_buff_accumulator + atk_ex_sa
                    ex_atk_val = calculate_dokkan_atk(base_atk, atk_ls, atk_mem, atk_add - atk_mem - atk_field - atk_act, atk_field, atk_act, atk_link, ex_ki_multi_to_use, atk_mult, total_multi)
                current_buff_accumulator += atk_ex_sa
                buff_queue_atk.append((turn_game, atk_ex_dur, atk_ex_sa))
                
            for u in range(atk_ultra_pt):
                if u == 0:
                    total_multi = atk_ultra_base + (sa_potential_lv * 5) + current_buff_accumulator + atk_ultra_sa
                    ultra_atk_val = calculate_dokkan_atk(base_atk, atk_ls, atk_mem, atk_add - atk_mem - atk_field - atk_act, atk_field, atk_act, atk_link, ultra_ki_multi, atk_mult, total_multi)
                current_buff_accumulator += atk_ultra_sa
                buff_queue_atk.append((turn_game, atk_ultra_dur, atk_ultra_sa))
                
            for n in range(atk_normal_pt):
                if n == 0:
                    total_multi = atk_normal_base + (sa_potential_lv * 5) + current_buff_accumulator + atk_normal_sa
                    normal_atk_val = calculate_dokkan_atk(base_atk, atk_ls, atk_mem, atk_add - atk_mem - atk_field - atk_act, atk_field, atk_act, atk_link, normal_ki_multi, atk_mult, total_multi)
                current_buff_accumulator += atk_normal_sa
                buff_queue_atk.append((turn_game, atk_normal_dur, atk_normal_sa))
            
            results_atk.append({
                "顔出し回数": f"{i}. 登場{i}回目", 
                "アクティブATK": active_atk_val if active_atk_val > 0 else 0,
                "EX必殺ATK": ex_atk_val if atk_ex_pt > 0 else 0,
                "超必殺ATK": ultra_atk_val if atk_ultra_pt > 0 else 0, 
                "通常必殺ATK": normal_atk_val if atk_normal_pt > 0 else 0
            })
        
        df_atk = pd.DataFrame(results_atk).set_index("顔出し回数")
        st.subheader("📊 シミュレーション結果")
        ar1, ar2 = st.columns([2, 1])
        with ar1: 
            st.line_chart(df_atk[["アクティブATK", "EX必殺ATK", "超必殺ATK", "通常必殺ATK"]])
        with ar2: 
            formatter = {
                "アクティブATK": lambda x: f"{x:,}" if isinstance(x, int) and x > 0 else "-",
                "EX必殺ATK": lambda x: f"{x:,}" if isinstance(x, int) and x > 0 else "-",
                "超必殺ATK": lambda x: f"{x:,}" if isinstance(x, int) and x > 0 else "-",
                "通常必殺ATK": lambda x: f"{x:,}" if isinstance(x, int) and x > 0 else "-"
            }
            st.dataframe(df_atk.style.format(formatter=formatter))

# ==========================================
# タブ3: 実戦ダメ計 (即席)
# ==========================================
with tab3:
    type_label = {"有利": "有利", "等倍": "等倍", "不利": "不利"}[enemy_element]
    same_class = element_def[0] == enemy_class[0]
    multi = {"有利": (0.9, 1.0), "等倍": (1.0, 1.15), "不利": (1.25, 1.5)}[enemy_element][0 if same_class else 1]
    render_practical_tab(dict(base=base_def, leader=def_ls, memory=def_mem, add=def_add, field=def_field, active=def_act, mult=def_mult, link=def_link, reduction=dmg_reduction_before, guard=guard_active, type_choice=f"{type_label} ({'同クラス' if same_class else '別クラス'}): {multi}倍", enemy_man=enemy_atk_man, crit=crit_active, crit_atk=ecrit_atk_up, crit_def=ecrit_def_down, ultra_effect=def_ultra_sa * def_ultra_pt + def_ex_sa * def_ex_pt, normal_effect=def_normal_sa * def_normal_pt))

# ==========================================
# タブ4: 検証ツール (敵ATK逆算)
# ==========================================
with tab4:
    st.markdown("### 🔍 敵ATKの逆算ツール")
    st.write("ゲーム内で実際に食らったダメージから、敵の必殺技ATKを逆算します。")
    
    rev_actual_dmg = st.number_input("実際に受けたダメージ", min_value=0, value=300000, step=10000, key="r_dmg")

    st.markdown("#### 自身のステータス参照")
    calc_mode = st.radio("DEF・軽減率の入力方法", ["手動で入力する", "DEFタブのシミュレーション結果から選ぶ"], horizontal=True, key="r_mode")

    target_def, target_dr = 0, 0

    if calc_mode == "DEFタブのシミュレーション結果から選ぶ":
        if not st.session_state.def_results:
            st.warning("⚠️ 先に「DEFタブ」でシミュレーションを実行してください。")
        else:
            turn_options = [r["顔出し回数"] for r in st.session_state.def_results]
            selected_turn = st.selectbox("ダメージを受けたターン", options=turn_options, key="r_turn")
            target_def = next(r["DEF"] for r in st.session_state.def_results if r["顔出し回数"] == selected_turn)
            target_dr = st.number_input("適用する軽減率(%)を微調整", value=0, step=10, key="r_dr_adj")
            st.info(f"👉 適用されるDEF: **{target_def:,}**")
    else:
        cr1, cr2 = st.columns(2)
        with cr1: target_def = st.number_input("受けた時点の自身のDEF", min_value=0, value=500000, step=10000, key="r_def")
        with cr2: target_dr = st.number_input("受けた時点の軽減率 (%)", min_value=0, max_value=99, value=0, step=10, key="r_dr")

    # ★ 逆算タブにも敵の会心設定を追加
    with st.expander("💥 受けた攻撃が会心だった場合"):
        r_crit = st.checkbox("受けた攻撃は会心だった", value=False, key="r_ecrit")
        c_rc1, c_rc2 = st.columns(2)
        with c_rc1: r_ecrit_atk_up = st.number_input("敵のATKアップ(%)", min_value=0, value=50, step=10, key="r_ec_atk")
        with c_rc2: r_ecrit_def_down = st.number_input("こちらのDEFダウン(%)", min_value=0, max_value=100, value=50, step=10, key="r_ec_def")

    if st.button("敵のATKを逆算する", type="secondary", use_container_width=True, key="btn_rev"):
        if rev_actual_dmg == 0:
            st.warning("⚠️ ダメージが0（完封）の場合、敵のATKは特定できません。")
        elif target_dr >= 100:
            st.warning("⚠️ 軽減率が100%以上の場合は計算できません。")
        else:
            e_class = st.session_state.get("last_enemy_class", "極系")
            e_element = st.session_state.get("last_enemy_element", "等倍")
            g_active = st.session_state.get("last_guard", False)
            u_class = st.session_state.get("last_user_class", "超速")
            
            is_same_class = (u_class[0] == e_class[0])
            
            if e_element == "有利":
                rev_base_m = 0.9 if is_same_class else 1.0
            elif e_element == "等倍":
                rev_base_m = 1.0 if is_same_class else 1.15
            else:
                rev_base_m = 1.25 if is_same_class else 1.5

            try:
                atk_lower, atk_upper = reverse_enemy_atk(rev_actual_dmg, target_def, target_dr, type_multi=rev_base_m, guard=g_active, advantageous=e_element == "有利", crit=r_crit, crit_atk=r_ecrit_atk_up, crit_def=r_ecrit_def_down)
                estimated_atk = (atk_lower + atk_upper) / 2
            except ValueError as error:
                st.error(str(error))
                st.stop()
            st.caption(f"同じ計算式で一致する敵ATK範囲: {atk_lower:,}〜{atk_upper:,}（乱数なし）。")

            st.success(f"🎯 推測される敵のATK: **約 {int(estimated_atk):,} (約 {estimated_atk / 10000:.1f} 万)**")
            if r_crit:
                st.info(f"※参照した属性相性: 敵【{e_class}/{e_element}】/ ガード【{'あり' if g_active else 'なし'}】 / 会心【あり】")
            else:
                st.info(f"※参照した属性相性: 敵【{e_class}/{e_element}】/ ガード【{'あり' if g_active else 'なし'}】 (DEFタブの設定が反映されています)")