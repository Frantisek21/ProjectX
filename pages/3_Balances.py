import streamlit as st
from db import init_db, get_all_groups, get_balances
from utils import show_sidebar, apply_theme

init_db()

st.set_page_config(page_title="Balances", page_icon="⚖️")
color = show_sidebar()
apply_theme(color)
st.title("Balances")

groups = get_all_groups()

if not groups:
    st.info("Create a group and add expenses first.")
    st.stop()

group_names = [g["name"] for g in groups]
selected_group_name = st.selectbox("Select Group", group_names)
group = next(g for g in groups if g["name"] == selected_group_name)

st.divider()

balances = get_balances(group["id"])

if not balances:
    st.success("All settled up! No one owes anything.")
else:
    st.subheader(f"Who owes whom in {selected_group_name}")
    for b in balances:
        st.markdown(f"**{b['debtor']}** owes **{b['creditor']}** `${b['amount']:.2f}`")
