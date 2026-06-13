import streamlit as st
from db import (
    init_db, get_all_groups, get_group_members, get_all_people_map,
    add_expense, get_group_expenses, set_expense_settled, get_balances,
)
from utils import show_sidebar, apply_theme, avatar_html, DEFAULT_COLOR

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

st.title(group["name"])

member_avatars = " ".join(
    avatar_html(m["name"], people_map.get(m["id"], {}).get("color", DEFAULT_COLOR),
                people_map.get(m["id"], {}).get("pfp"))
    + f" {m['name']}"
    for m in members
)
st.markdown(member_avatars, unsafe_allow_html=True)

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
                        add_expense(group["id"], description.strip(), amount, name_to_id[paid_by_name], splits)
                        st.success(f"Added '{description.strip()}' — {amount:.2f} {symbol}")
                        st.rerun()

# ── Expense List ───────────────────────────────────────────────────────────────
st.subheader("Expenses")
expenses = get_group_expenses(group["id"])

if not expenses:
    st.info("No expenses yet — add one above.")
else:
    for exp in expenses:
        is_settled = bool(exp["settled"])
        payer = people_map.get(exp["paid_by_id"], {})
        av = avatar_html(exp["paid_by_name"], payer.get("color", DEFAULT_COLOR), payer.get("pfp"), size=26)

        col_main, col_btn = st.columns([5, 1])
        with col_main:
            opacity = "0.4" if is_settled else "1"
            decoration = "line-through" if is_settled else "none"
            st.markdown(
                f'<div style="opacity:{opacity};text-decoration:{decoration}">'
                f'{av} <strong>{exp["description"]}</strong> — {exp["amount"]:.2f} {symbol} '
                f'paid by {exp["paid_by_name"]}'
                f'<br><small style="color:gray">{exp["created_at"]}</small>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col_btn:
            label = "Unsettle" if is_settled else "Settle"
            if st.button(label, key=f"settle_{exp['id']}", type="secondary"):
                set_expense_settled(exp["id"], not is_settled)
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
        av_d = avatar_html(b["debtor"], debtor.get("color", DEFAULT_COLOR), debtor.get("pfp"), size=26)
        av_c = avatar_html(b["creditor"], creditor.get("color", DEFAULT_COLOR), creditor.get("pfp"), size=26)
        st.markdown(
            f'{av_d} <strong>{b["debtor"]}</strong> owes '
            f'{av_c} <strong>{b["creditor"]}</strong> '
            f'<code>{b["amount"]:.2f} {symbol}</code>',
            unsafe_allow_html=True,
        )
