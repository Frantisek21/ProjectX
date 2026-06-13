import streamlit as st
from db import init_db, get_all_groups, get_group_members
from utils import show_sidebar, apply_theme

init_db()

st.set_page_config(page_title="SplitEasy", page_icon="💸", layout="centered")
info = show_sidebar()
apply_theme(info["color"])

st.title("SplitEasy")
st.caption("Track shared expenses and settle up easily.")

st.divider()

groups = get_all_groups()

if not groups:
    st.info("No groups yet. Head to **Groups** in the sidebar to create one.")
else:
    st.subheader("Your Groups")
    for group in groups:
        members = get_group_members(group["id"])
        member_names = ", ".join(m["name"] for m in members) or "No members"
        st.markdown(f"**{group['name']}** — {member_names}")
