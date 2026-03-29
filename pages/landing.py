import streamlit as st

def show():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<div class="brand">🏟️ TurfBook</div>', unsafe_allow_html=True)
        st.markdown("### Book your turf slot in seconds.")
        st.markdown("Find available slots, pay online, and get a WhatsApp confirmation instantly.")
        st.markdown("<br>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🗓️ Book a Slot", use_container_width=True, type="primary"):
                st.session_state.page = "book"
                st.rerun()
        with c2:
            if st.button("⚙️ Owner Login", use_container_width=True):
                st.session_state.page = "owner_login"
                st.rerun()

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("""
        <div style="display:flex;gap:2rem;justify-content:center;text-align:center;padding:1rem 0">
          <div><b>⚡ Instant</b><br><span style="color:#888;font-size:0.85rem">Real-time availability</span></div>
          <div><b>💳 Secure</b><br><span style="color:#888;font-size:0.85rem">Razorpay payments</span></div>
          <div><b>📲 WhatsApp</b><br><span style="color:#888;font-size:0.85rem">Instant confirmation</span></div>
        </div>
        """, unsafe_allow_html=True)
