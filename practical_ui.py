import pandas as pd
import streamlit as st
from damage_core import LABELS, basis_def, timeline

SCREEN = "画面のDEFから計算"
BASIS = "DEFタブの基礎ステータスから計算"

def event(order, label, group, value):
    return {"有効": True, "順番": order, "タイミング": label, "補正先": group, "変化量(%)": value}

def number_input(label, *, key, value=0, **kwargs):
    if key in st.session_state:
        return st.number_input(label, key=key, **kwargs)
    return st.number_input(label, key=key, value=value, **kwargs)

def render_practical_tab(sim):
    st.markdown("### 📱 被弾するタイミングごとのダメージ計算")
    st.write("確認できる画面のDEFを出発点に、味方の行動・自身の必殺・支援発動を順番に加えます。")
    if st.button("DEFタブの確認時点の設定を読み込む", key="p_import_sim"):
        mapping = {"p_add_c": "add", "p_mult_c": "mult", "p_mem_c": "memory", "p_field_c": "field", "p_active_c": "active", "p_link_c": "link"}
        for widget, field in mapping.items():
            st.session_state[widget] = sim[field]
        st.session_state.update(p_source=BASIS, p_sa_p=0, p_receive=0, p_once=0, p_dr=sim["reduction"], p_g_act=sim["guard"], p_type=sim["type_choice"], p_eatk=sim["enemy_man"], p_ecrit=sim["crit"], p_ec_atk=sim["crit_atk"], p_ec_def=sim["crit_def"])
        st.session_state["p_event_seed"] = [event(10, "超必殺後", "必殺技効果・味方の必殺支援", sim["ultra_effect"]), event(20, "通常必殺・追撃後", "必殺技効果・味方の必殺支援", sim["normal_effect"])]
        st.session_state.pop("p_events", None)
    source = st.radio("計算の出発点", [SCREEN, BASIS], key="p_source")
    if source == SCREEN:
        screen = number_input("画面のDEF実数値", min_value=0, value=250000, step=10000, key="p_cdef")
        st.caption("画面DEFは途中で端数が切り捨てられているため、基礎DEFからの計算とは数ポイントの差が出る場合があります。")
    else:
        screen = 0
        st.caption(f"DEFタブの基礎DEF {sim['base']:,}、リーダースキル {sim['leader']}%を使います。反映済み効果は下で指定します。")
    st.markdown("#### ① 確認時点で反映済みの効果")
    cols = st.columns(3)
    with cols[0]: add = number_input("足し算パッシブ (%)", min_value=0, value=150, step=10, key="p_add_c")
    with cols[1]: mult = number_input("掛け算パッシブ (%)", min_value=0, value=0, step=10, key="p_mult_c")
    with cols[2]: sa = number_input("有効な必殺技・必殺支援の合計 (%)", min_value=0, value=0, step=10, key="p_sa_p")
    current = dict(add=add, mult=mult, sa=sa)
    with st.expander("反映済みのメモリー・フィールド・アクティブ・リンク"):
        for field, label, key in [("memory", "メモリー", "p_mem_c"), ("field", "フィールド", "p_field_c"), ("active", "アクティブ", "p_active_c"), ("link", "リンク", "p_link_c")]:
            current[field] = number_input(label + " (%)", min_value=0, value=0, step=1, key=key)
    basis = (sim["base"], sim["leader"]) if source == BASIS else None
    visible_def = basis_def(*basis, current) if basis else screen
    st.metric("確認時点DEF", f"{visible_def:,}")
    st.markdown("#### ② 被弾するときに発動する効果")
    cols = st.columns(2)
    with cols[0]: receive = number_input("被弾時の掛け算パッシブ (%)", min_value=0, value=0, step=10, key="p_receive")
    with cols[1]: once = number_input("1回限定など、条件付きの被弾時補正 (%)", min_value=0, value=0, step=10, key="p_once")
    once_active = st.checkbox("条件付き補正がこの被弾で有効", value=False, key="p_once_active")
    st.caption("画面に反映されていない効果だけを入力します。1回限定効果が有効かは、比較したい被弾に合わせて指定してください。")
    st.markdown("#### ③ 確認後に発動する効果")
    st.write("発動順に行を追加します。同時に発動する効果は同じ順番にしてください。同じ補正先の倍率は合算します。通常必殺でDEFが上がらないキャラは0%です。")
    st.caption("被弾で発動する支援は、効果が発動した時点の行へ。味方の必殺技によるDEF支援は『必殺技効果・味方の必殺支援』へ入力します。効果が切れる場合はマイナスの変化量を入力します。")
    seed = st.session_state.get("p_event_seed", [event(10, "味方の行動後", "足し算パッシブ", 0), event(20, "自身の超必殺後", "必殺技効果・味方の必殺支援", 30), event(30, "通常必殺・追撃後", "必殺技効果・味方の必殺支援", 0)])
    events = st.data_editor(pd.DataFrame(seed), num_rows="dynamic", hide_index=True, key="p_events", column_config={"有効": st.column_config.CheckboxColumn("有効", default=True), "順番": st.column_config.NumberColumn("順番", min_value=1, step=1, required=True), "タイミング": st.column_config.TextColumn("タイミング", required=True), "補正先": st.column_config.SelectboxColumn("補正先", options=list(LABELS) + ["軽減率"], required=True), "変化量(%)": st.column_config.NumberColumn("変化量(%)", step=1, required=True)})
    st.markdown("#### ④ 敵の攻撃と防御設定")
    cols = st.columns(2)
    with cols[0]: enemy = number_input("敵必殺ATK (万単位)", min_value=0, value=150, step=10, key="p_eatk") * 10000
    with cols[1]: dr = number_input("確認時点の軽減率 (%)", min_value=0, max_value=100, value=0, step=5, key="p_dr")
    options = {"有利 (同クラス): 0.9倍": .9, "有利 (別クラス): 1.0倍": 1., "等倍 (同クラス): 1.0倍": 1., "等倍 (別クラス): 1.15倍": 1.15, "不利 (同クラス): 1.25倍": 1.25, "不利 (別クラス): 1.5倍": 1.5}
    chosen = st.selectbox("属性とクラスの相性", list(options), index=None if "p_type" in st.session_state else 3, key="p_type")
    guard = st.checkbox("🛡️ 全属性ガード発動", value=False, key="p_g_act")
    with st.expander("敵の会心設定"):
        crit = st.checkbox("敵が会心を発動する", value=False, key="p_ecrit")
        atk_up = number_input("敵のATKアップ (%)", min_value=0, value=50, key="p_ec_atk")
        def_down = number_input("こちらのDEFダウン (%)", min_value=0, max_value=100, value=50, key="p_ec_def")
    try:
        rows = timeline(screen, current, events.to_dict("records"), enemy, dr, basis=basis, receiving=receive + (once if once_active else 0), type_multi=options[chosen], guard=guard, advantageous=chosen.startswith("有利"), crit=crit, crit_atk=atk_up, crit_def=def_down)
    except ValueError as error:
        st.error(str(error))
        return
    st.markdown("#### 被弾タイミングごとの結果")
    st.caption("各行は、その時点で被弾した場合の比較です。上から順に敵の攻撃を受ける想定ではありません。乱数・属性防御UPなどは含まない参考値です。")
    selected = st.selectbox("比較したい被弾タイミング", range(len(rows)), index=len(rows)-1, format_func=lambda index: f"{index}. {rows[index]['タイミング']}", key="p_selected")
    result = rows[selected]
    cols = st.columns(2)
    with cols[0]: st.metric("被弾時DEF", f"{result['被弾時DEF']:,}")
    with cols[1]: st.metric("被ダメージ（参考値）", "2桁ダメージ相当" if result["被ダメージ"] == 0 else f"{result['被ダメージ']:,}")
    st.dataframe(pd.DataFrame(rows).style.format({key: "{:,}" for key in rows[0] if key != "タイミング"}), hide_index=True)
    st.caption("敵ATK × 属性補正（全属性ガード時は0.8）× 軽減 → DEFを引く → ガード時は0.5。")
