import streamlit as st
from utils.auth import owner_login, set_owner_session
from utils.db import get_turfs_by_owner

def show():
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown('<div class="brand">🏟️ TurfBook</div>', unsafe_allow_html=True)
    with c2:
        if st.button("← Back"):
            st.session_state.page = "landing"
            st.rerun()

    st.markdown("### Owner Login")
    st.markdown("Manage your turf, view bookings, and track revenue.")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("owner_login_form"):
            email    = st.text_input("Email", placeholder="owner@myturf.com")
            password = st.text_input("Password", type="password")
            submit   = st.form_submit_button("Login →", type="primary", use_container_width=True)

        if submit:
            if not email or not password:
                st.error("Please enter both email and password.")
            else:
                owner = owner_login(email.strip().lower(), password)
                if not owner:
                    st.error("Invalid email or password.")
                else:
                    turfs = get_turfs_by_owner(owner["id"])
                    if not turfs:
                        st.error("No turf found for this account. Contact support.")
                    else:
                        set_owner_session(owner, turfs[0])
                        st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("Don't have an account? Contact us to get your turf onboarded.")
