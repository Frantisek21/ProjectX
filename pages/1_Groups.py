import streamlit as st
from db import (
    init_db, add_person, create_group, get_all_people,
    get_all_groups, get_group_members, get_all_people_map, delete_group,
)
from utils import show_sidebar, apply_theme, person_chip, DEFAULT_COLOR

init_db()

st.set_page_config(page_title="Groups", page_icon="👥")
info = show_sidebar()
apply_theme(info["color"])
st.title("Groups")

# ── Add a person ───────────────────────────────────────────────────────────────
st.subheader("Add a Person")
with st.form("add_person_form", clear_on_submit=True):
    new_name = st.text_input("Name")
    if st.form_submit_button("Add Person"):
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

# ── Create a group ─────────────────────────────────────────────────────────────
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
        if st.form_submit_button("Create Group"):
            if not group_name.strip():
                st.warning("Please enter a group name.")
            elif len(selected) < 2:
                st.warning("Select at least 2 members.")
            else:
                name_to_id = {p["name"]: p["id"] for p in people}
                create_group(group_name.strip(), [name_to_id[n] for n in selected])
                st.success(f"Group '{group_name.strip()}' created!")
                st.rerun()

st.divider()

# ── Existing groups ────────────────────────────────────────────────────────────
st.subheader("Existing Groups")
groups = get_all_groups()

if not groups:
    st.info("No groups yet.")
else:
    people_map = get_all_people_map()
    confirm_id = st.session_state.get("confirm_delete_group")

    for group in groups:
        members = get_group_members(group["id"])

        col_name, col_del = st.columns([5, 1])
        with col_name:
            st.markdown(f"**{group['name']}**")
        with col_del:
            if confirm_id == group["id"]:
                pass  # buttons shown below
            else:
                if st.button("Delete", key=f"del_grp_{group['id']}", type="secondary"):
                    st.session_state.confirm_delete_group = group["id"]
                    st.rerun()

        if members:
            chips = "&nbsp;&nbsp;".join(
                person_chip(m["name"], people_map.get(m["id"], {}).get("color", DEFAULT_COLOR),
                            people_map.get(m["id"], {}).get("pfp"), size=24)
                for m in members
            )
            st.markdown(
                f'<div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:4px">{chips}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.caption("No members")

        if confirm_id == group["id"]:
            st.warning(f"Delete **{group['name']}**? This will permanently remove all its expenses.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Confirm Delete", key=f"confirm_del_{group['id']}"):
                    if st.session_state.get("active_group_id") == group["id"]:
                        st.session_state.pop("active_group_id", None)
                    delete_group(group["id"])
                    st.session_state.confirm_delete_group = None
                    st.rerun()
            with c2:
                if st.button("Cancel", key=f"cancel_del_{group['id']}"):
                    st.session_state.confirm_delete_group = None
                    st.rerun()

        st.markdown("---")
