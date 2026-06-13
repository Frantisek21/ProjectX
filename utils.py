import base64
import streamlit as st
from db import get_all_people, get_all_groups, update_person_profile, get_setting, set_setting

DEFAULT_COLOR = "#4A90D9"

CURRENCIES = ["CZK", "EUR", "USD", "GBP", "PLN"]
CURRENCY_SYMBOLS = {"CZK": "Kč", "EUR": "€", "USD": "$", "GBP": "£", "PLN": "zł"}


def apply_theme(color: str):
    st.markdown(f"""
    <style>
        div[data-testid="stDecoration"] {{
            background: linear-gradient(90deg, {color}, {color}88) !important;
        }}
        .stButton > button:not([kind="secondary"]) {{
            background-color: {color} !important;
            border-color: {color} !important;
            color: white !important;
        }}
        .stButton > button:not([kind="secondary"]):hover {{
            filter: brightness(1.1);
        }}
        div[data-baseweb="select"] > div:first-child {{
            border-color: {color}88 !important;
        }}
        div[data-testid="stNumberInput"] input:focus,
        div[data-testid="stTextInput"] input:focus,
        textarea:focus {{
            border-color: {color} !important;
            box-shadow: 0 0 0 1px {color}66 !important;
        }}
        h1 {{ border-bottom: 3px solid {color}; padding-bottom: 6px; }}
    </style>
    """, unsafe_allow_html=True)


def show_sidebar() -> dict:
    people = get_all_people()
    groups = get_all_groups()

    with st.sidebar:
        # --- Profile ---
        st.markdown("### Profile")

        color = DEFAULT_COLOR

        if people:
            person_names = [p["name"] for p in people]
            if "current_user_id" not in st.session_state:
                st.session_state.current_user_id = people[0]["id"]

            default_index = next(
                (i for i, p in enumerate(people) if p["id"] == st.session_state.current_user_id), 0
            )
            selected_name = st.selectbox("Logged in as", person_names, index=default_index)
            person = next(p for p in people if p["name"] == selected_name)
            st.session_state.current_user_id = person["id"]

            color = person["color"] or DEFAULT_COLOR

            if person["pfp"]:
                img_bytes = base64.b64decode(person["pfp"])
                st.image(img_bytes, width=90)

            with st.expander("Edit Profile"):
                new_color = st.color_picker("App color", value=color, key="sidebar_color")
                new_pfp = st.file_uploader(
                    "Profile picture", type=["png", "jpg", "jpeg"], key="sidebar_pfp"
                )
                if st.button("Save", key="sidebar_save"):
                    pfp_b64 = None
                    if new_pfp:
                        pfp_b64 = base64.b64encode(new_pfp.read()).decode()
                    update_person_profile(person["id"], new_color, pfp_b64)
                    st.success("Saved!")
                    st.rerun()
        else:
            st.info("Add people in the Groups page.")

        st.divider()

        # --- Groups ---
        st.markdown("### Groups")
        if not groups:
            st.caption("No groups yet — create one in Groups.")
        else:
            if "active_group_id" not in st.session_state:
                st.session_state.active_group_id = groups[0]["id"]

            for group in groups:
                is_active = st.session_state.active_group_id == group["id"]
                label = f"**> {group['name']}**" if is_active else group["name"]
                if st.button(label, key=f"grp_{group['id']}", use_container_width=True):
                    st.session_state.active_group_id = group["id"]
                    st.rerun()

        st.divider()

        # --- Currency ---
        st.markdown("### Currency")
        saved_currency = get_setting("currency", "CZK")
        currency_index = CURRENCIES.index(saved_currency) if saved_currency in CURRENCIES else 0
        selected_currency = st.selectbox("", CURRENCIES, index=currency_index, label_visibility="collapsed")
        if selected_currency != saved_currency:
            set_setting("currency", selected_currency)
            st.rerun()
        st.session_state.currency = selected_currency

    currency_symbol = CURRENCY_SYMBOLS[selected_currency]
    return {"color": color, "currency": selected_currency, "symbol": currency_symbol}
