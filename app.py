import streamlit as st
st.set_page_config(
    page_title="TurfBook",
    page_icon="🏟️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

from utils.supabase_client import get_supabase
from utils.auth import check_session
from pages import customer_booking, owner_dashboard, owner_login, landing

# ── session defaults ────────────────────────────────────────────────────────
for k, v in {
    "role": None,          # "customer" | "owner"
    "owner_id": None,
    "turf_id": None,
    "turf": None,
    "cust_name": None,
    "cust_phone": None,
    "page": "landing",     # "landing" | "book" | "owner_login" | "dashboard"
    "booking_slot": None,
    "booking_date": None,
    "razorpay_order": None,
    "payment_verified": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── global CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600&family=Syne:wght@700&display=swap');

html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
h1,h2,h3 { font-family: 'Syne', sans-serif; }

.stButton > button {
    border-radius: 10px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 500 !important;
    transition: all 0.2s;
}
.stButton > button:hover { transform: translateY(-1px); }

div[data-testid="stMetricValue"] { font-family: 'Syne', sans-serif; font-size: 2rem; }

.brand { font-family: 'Syne', sans-serif; color: #1D9E75; font-size: 1.6rem; font-weight: 700; }
.slot-available {
    background: #E1F5EE; color: #0F6E56; border: 1.5px solid #1D9E75;
    border-radius: 10px; padding: 10px; text-align: center;
    cursor: pointer; font-weight: 600; font-size: 0.85rem;
}
.slot-booked {
    background: #FCEBEB; color: #A32D2D; border: 1.5px solid #f09595;
    border-radius: 10px; padding: 10px; text-align: center;
    font-weight: 600; font-size: 0.85rem; opacity: 0.7;
}
.slot-selected {
    background: #1D9E75; color: #fff; border: 2px solid #0F6E56;
    border-radius: 10px; padding: 10px; text-align: center;
    cursor: pointer; font-weight: 700; font-size: 0.85rem;
}
.summary-card {
    background: #E1F5EE; border-radius: 14px; padding: 18px 22px;
    border: 1px solid #9FE1CB; margin: 12px 0;
}
.summary-row { display:flex; justify-content:space-between; font-size:0.9rem; margin-bottom:6px; color:#0F6E56; }
.summary-total { font-weight:700; font-size:1.05rem; border-top:1px solid #9FE1CB; padding-top:8px; margin-top:8px; }
.booking-card {
    background: white; border-radius: 12px; padding: 14px 18px;
    border: 0.5px solid #e0e0e0; margin-bottom: 10px;
}
.badge-green { background:#E1F5EE; color:#0F6E56; padding:3px 12px; border-radius:20px; font-size:0.75rem; font-weight:600; }
.badge-red   { background:#FCEBEB; color:#A32D2D; padding:3px 12px; border-radius:20px; font-size:0.75rem; font-weight:600; }
.badge-amber { background:#FAEEDA; color:#854F0B; padding:3px 12px; border-radius:20px; font-size:0.75rem; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ── router ───────────────────────────────────────────────────────────────────
page = st.session_state.page

if page == "landing":
    landing.show()
elif page == "book":
    customer_booking.show()
elif page == "owner_login":
    owner_login.show()
elif page == "dashboard":
    owner_dashboard.show()
