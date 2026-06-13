import streamlit as st
from db import init_db, get_all_groups, get_balances
from utils import show_sidebar, apply_theme

init_db()

st.set_page_config(page_title="Balances", page_icon="⚖️")
info = show_sidebar()
apply_theme(info["color"])
symbol = info["symbol"]

st.title("Balances")

groups = get_all_groups()
if not groups:
    st.info("Create a group and add expenses first.")
    st.stop()

active_id = st.session_state.get("active_group_id", groups[0]["id"])
group = next((g for g in groups if g["id"] == active_id), groups[0])

st.caption(f"Active group: **{group['name']}** — switch groups in the sidebar")
st.divider()

balances = get_balances(group["id"])

if not balances:
    st.success("All settled up! No one owes anything.")
else:
    st.subheader(f"Who owes whom in {group['name']}")
    st.caption("Settled expenses are excluded from these calculations.")
    for b in balances:
        st.markdown(f"**{b['debtor']}** owes **{b['creditor']}** `{b['amount']:.2f} {symbol}`")
