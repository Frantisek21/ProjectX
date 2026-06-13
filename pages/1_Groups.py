import streamlit as st
from db import init_db, add_person, create_group, get_all_people, get_all_groups, get_group_members
from utils import show_sidebar, apply_theme

init_db()

st.set_page_config(page_title="Groups", page_icon="👥")
color = show_sidebar()
apply_theme(color)
st.title("Groups")

# --- Add a person ---
st.subheader("Add a Person")
with st.form("add_person_form", clear_on_submit=True):
    new_name = st.text_input("Name")
    submitted = st.form_submit_button("Add Person")
    if submitted:
        if new_name.strip():
            try:
                add_person(new_name.strip())
                st.success(f"Added {new_name.strip()}!")
                st.rerun()
            except Exception:
                st.error("That name already exists.")
        else:
            st.warning("Please enter a name.")

st.divider()

# --- Create a group ---
st.subheader("Create a Group")
people = get_all_people()

if not people:
    st.info("Add some people above before creating a group.")
else:
    with st.form("create_group_form", clear_on_submit=True):
        group_name = st.text_input("Group name")
        selected = st.multiselect(
            "Members",
            options=[p["name"] for p in people],
            default=[p["name"] for p in people],
        )
        submitted = st.form_submit_button("Create Group")
        if submitted:
            if not group_name.strip():
                st.warning("Please enter a group name.")
            elif len(selected) < 2:
                st.warning("Select at least 2 members.")
            else:
                name_to_id = {p["name"]: p["id"] for p in people}
                member_ids = [name_to_id[n] for n in selected]
                create_group(group_name.strip(), member_ids)
                st.success(f"Group '{group_name.strip()}' created!")
                st.rerun()

st.divider()

# --- Existing groups ---
st.subheader("Existing Groups")
groups = get_all_groups()

if not groups:
    st.info("No groups yet.")
else:
    for group in groups:
        members = get_group_members(group["id"])
        member_names = ", ".join(m["name"] for m in members) or "No members"
        st.markdown(f"**{group['name']}** — {member_names}")
