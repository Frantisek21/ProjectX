import streamlit as st
from db import init_db, get_all_groups, get_group_members, add_expense, get_group_expenses, set_expense_settled
from utils import show_sidebar, apply_theme

init_db()

st.set_page_config(page_title="Add Expense", page_icon="➕")
info = show_sidebar()
apply_theme(info["color"])
symbol = info["symbol"]

st.title("Add Expense")

groups = get_all_groups()
if not groups:
    st.info("Create a group first in the **Groups** page.")
    st.stop()

active_id = st.session_state.get("active_group_id", groups[0]["id"])
group = next((g for g in groups if g["id"] == active_id), groups[0])
members = get_group_members(group["id"])

st.caption(f"Active group: **{group['name']}** — switch groups in the sidebar")

if len(members) < 2:
    st.warning("This group needs at least 2 members.")
    st.stop()

st.divider()

with st.form("add_expense_form", clear_on_submit=True):
    description = st.text_input("Description (e.g. Dinner, Taxi)")
    amount = st.number_input(f"Total Amount ({symbol})", min_value=0.01, step=0.01, format="%.2f")
    paid_by_name = st.selectbox("Paid by", [m["name"] for m in members])

    st.markdown("**Split between:**")
    member_selected = {}
    cols = st.columns(min(len(members), 4))
    for i, member in enumerate(members):
        with cols[i % len(cols)]:
            member_selected[member["name"]] = st.checkbox(member["name"], value=True)

    submitted = st.form_submit_button("Add Expense")

    if submitted:
        if not description.strip():
            st.warning("Please enter a description.")
        else:
            splitting_names = [n for n, checked in member_selected.items() if checked]
            if not splitting_names:
                st.warning("Select at least one person to split with.")
            else:
                name_to_id = {m["name"]: m["id"] for m in members}
                split_count = len(splitting_names)
                per_person = round(amount / split_count, 2)
                splits = {name_to_id[n]: per_person for n in splitting_names}
                remainder = round(amount - per_person * split_count, 2)
                splits[name_to_id[splitting_names[0]]] += remainder

                paid_by_id = name_to_id[paid_by_name]
                add_expense(group["id"], description.strip(), amount, paid_by_id, splits)
                st.success(f"Added '{description.strip()}' — {amount:.2f} {symbol} split {split_count} ways.")
                st.rerun()

st.divider()

# --- Expense list with settle toggles ---
st.subheader(f"Expenses in {group['name']}")
expenses = get_group_expenses(group["id"])

if not expenses:
    st.info("No expenses yet.")
else:
    for exp in expenses:
        is_settled = bool(exp["settled"])
        col_main, col_toggle = st.columns([5, 1])
        with col_main:
            if is_settled:
                st.markdown(
                    f"<span style='opacity:0.4;text-decoration:line-through'>"
                    f"**{exp['description']}** — {exp['amount']:.2f} {symbol} paid by {exp['paid_by_name']}"
                    f"</span>  \n<small style='opacity:0.4'>{exp['created_at']}</small>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"**{exp['description']}** — {exp['amount']:.2f} {symbol} paid by {exp['paid_by_name']}  \n"
                    f"<small>{exp['created_at']}</small>",
                    unsafe_allow_html=True,
                )
        with col_toggle:
            label = "Settled" if is_settled else "Settle"
            if st.button(label, key=f"settle_{exp['id']}", type="secondary"):
                set_expense_settled(exp["id"], not is_settled)
                st.rerun()
