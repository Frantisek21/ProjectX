import streamlit as st
from db import (
    init_db, get_all_groups, get_group_members, get_all_people_map,
    add_expense, get_group_expenses, set_expense_settled,
    update_expense, delete_expense, get_expense_splits, get_balances,
)
from utils import show_sidebar, apply_theme, avatar_html, person_chip, DEFAULT_COLOR

init_db()

st.set_page_config(page_title="SplitEasy", page_icon="💸", layout="centered")
info = show_sidebar()
apply_theme(info["color"])
symbol = info["symbol"]

groups = get_all_groups()

if not groups:
    st.title("SplitEasy")
    st.info("Head to **Groups** in the sidebar to create your first group.")
    st.stop()

active_id = st.session_state.get("active_group_id", groups[0]["id"])
group = next((g for g in groups if g["id"] == active_id), groups[0])
members = get_group_members(group["id"])
people_map = get_all_people_map()
name_to_id = {m["name"]: m["id"] for m in members}

# ── Group header ───────────────────────────────────────────────────────────────
st.title(group["name"])

chips = "&nbsp;&nbsp;".join(
    person_chip(m["name"], people_map.get(m["id"], {}).get("color", DEFAULT_COLOR),
                people_map.get(m["id"], {}).get("pfp"), size=26)
    for m in members
)
st.markdown(f'<div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:4px">{chips}</div>',
            unsafe_allow_html=True)

st.divider()

# ── Add Expense ────────────────────────────────────────────────────────────────
with st.expander("Add new expense", expanded=False):
    if len(members) < 2:
        st.warning("This group needs at least 2 members.")
    else:
        with st.form("add_expense_form", clear_on_submit=True):
            description = st.text_input("Description (e.g. Dinner, Taxi)")
            amount = st.number_input(f"Total amount ({symbol})", min_value=0.01, step=0.01, format="%.2f")
            paid_by_name = st.selectbox("Paid by", [m["name"] for m in members])

            st.markdown("**Split between:**")
            member_selected = {}
            cols = st.columns(min(len(members), 4))
            for i, member in enumerate(members):
                with cols[i % len(cols)]:
                    member_selected[member["name"]] = st.checkbox(member["name"], value=True)

            if st.form_submit_button("Add Expense"):
                if not description.strip():
                    st.warning("Please enter a description.")
                else:
                    splitting_names = [n for n, checked in member_selected.items() if checked]
                    if not splitting_names:
                        st.warning("Select at least one person to split with.")
                    else:
                        split_count = len(splitting_names)
                        per_person = round(amount / split_count, 2)
                        splits = {name_to_id[n]: per_person for n in splitting_names}
                        splits[name_to_id[splitting_names[0]]] += round(amount - per_person * split_count, 2)
                        add_expense(group["id"], description.strip(), amount, name_to_id[paid_by_name], splits)
                        st.success(f"Added '{description.strip()}' — {amount:.2f} {symbol}")
                        st.rerun()

# ── Expense List ───────────────────────────────────────────────────────────────
st.subheader("Expenses")
expenses = get_group_expenses(group["id"])

if not expenses:
    st.info("No expenses yet — add one above.")
else:
    editing_id = st.session_state.get("editing_expense_id")

    for exp in expenses:
        is_settled = bool(exp["settled"])
        payer = people_map.get(exp["paid_by_id"], {})

        if editing_id == exp["id"]:
            # ── Inline edit form ───────────────────────────────────────────────
            current_splits = get_expense_splits(exp["id"])
            with st.form(key=f"edit_form_{exp['id']}"):
                st.markdown(f"**Editing:** {exp['description']}")
                new_desc = st.text_input("Description", value=exp["description"])
                new_amount = st.number_input(
                    f"Amount ({symbol})", value=float(exp["amount"]), min_value=0.01, step=0.01, format="%.2f"
                )
                payer_index = next((i for i, m in enumerate(members) if m["id"] == exp["paid_by_id"]), 0)
                new_payer_name = st.selectbox("Paid by", [m["name"] for m in members], index=payer_index)

                st.markdown("**Split between:**")
                edit_selected = {}
                cols = st.columns(min(len(members), 4))
                for i, member in enumerate(members):
                    with cols[i % len(cols)]:
                        edit_selected[member["name"]] = st.checkbox(
                            member["name"],
                            value=member["id"] in current_splits,
                            key=f"es_{exp['id']}_{member['id']}",
                        )

                col_save, col_cancel = st.columns(2)
                save = col_save.form_submit_button("Save")
                cancel = col_cancel.form_submit_button("Cancel")

                if save:
                    splitting = [n for n, checked in edit_selected.items() if checked]
                    if splitting and new_desc.strip():
                        split_count = len(splitting)
                        per_person = round(new_amount / split_count, 2)
                        splits = {name_to_id[n]: per_person for n in splitting}
                        splits[name_to_id[splitting[0]]] += round(new_amount - per_person * split_count, 2)
                        update_expense(exp["id"], new_desc.strip(), new_amount, name_to_id[new_payer_name], splits)
                        st.session_state.editing_expense_id = None
                        st.rerun()
                if cancel:
                    st.session_state.editing_expense_id = None
                    st.rerun()
        else:
            # ── Normal expense row ─────────────────────────────────────────────
            col_main, col_settle, col_edit, col_del = st.columns([5, 1, 1, 1])
            with col_main:
                opacity = "0.4" if is_settled else "1"
                decoration = "line-through" if is_settled else "none"
                av = avatar_html(exp["paid_by_name"], payer.get("color", DEFAULT_COLOR), payer.get("pfp"), size=26)
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;opacity:{opacity};text-decoration:{decoration}">'
                    f'{av}'
                    f'<div><strong>{exp["description"]}</strong> — {exp["amount"]:.2f} {symbol} '
                    f'paid by {exp["paid_by_name"]}<br>'
                    f'<small style="color:gray">{exp["created_at"]}</small></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with col_settle:
                label = "Unsettle" if is_settled else "Settle"
                if st.button(label, key=f"settle_{exp['id']}", type="secondary"):
                    set_expense_settled(exp["id"], not is_settled)
                    st.rerun()
            with col_edit:
                if st.button("Edit", key=f"edit_{exp['id']}", type="secondary"):
                    st.session_state.editing_expense_id = exp["id"]
                    st.rerun()
            with col_del:
                if st.button("Del", key=f"del_{exp['id']}", type="secondary"):
                    delete_expense(exp["id"])
                    st.rerun()

st.divider()

# ── Balances ───────────────────────────────────────────────────────────────────
st.subheader("Balances")
balances = get_balances(group["id"])

if not balances:
    st.success("All settled up!")
else:
    st.caption("Settled expenses are excluded.")
    for b in balances:
        debtor = people_map.get(b["debtor_id"], {})
        creditor = people_map.get(b["creditor_id"], {})
        chip_d = person_chip(b["debtor"], debtor.get("color", DEFAULT_COLOR), debtor.get("pfp"), size=26)
        chip_c = person_chip(b["creditor"], creditor.get("color", DEFAULT_COLOR), creditor.get("pfp"), size=26)
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin:6px 0">'
            f'{chip_d}<span>owes</span>{chip_c}'
            f'<code style="margin-left:4px">{b["amount"]:.2f} {symbol}</code>'
            f'</div>',
            unsafe_allow_html=True,
        )
