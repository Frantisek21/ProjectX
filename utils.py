import base64
import streamlit as st
from db import get_all_people, update_person_profile

DEFAULT_COLOR = "#4A90D9"


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
        .stCheckbox span[data-testid="stWidgetLabel"] {{ color: inherit; }}
    </style>
    """, unsafe_allow_html=True)


def show_sidebar() -> str:
    people = get_all_people()

    with st.sidebar:
        if not people:
            st.info("Add people in the Groups page.")
            return DEFAULT_COLOR

        st.markdown("### Profile")

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

        st.divider()
        return color
