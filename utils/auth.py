import streamlit as st
import bcrypt
from utils.supabase_client import get_supabase

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def owner_login(email: str, password: str):
    """Returns owner dict if credentials valid, else None."""
    sb = get_supabase()
    res = sb.table("owners").select("*").eq("email", email).execute()
    if not res.data:
        return None
    owner = res.data[0]
    if not verify_password(password, owner["password_hash"]):
        return None
    return owner

def set_owner_session(owner: dict, turf: dict):
    st.session_state.role     = "owner"
    st.session_state.owner_id = owner["id"]
    st.session_state.turf_id  = turf["id"]
    st.session_state.turf     = turf
    st.session_state.page     = "dashboard"

def logout():
    for k in ["role","owner_id","turf_id","turf","cust_name","cust_phone",
              "page","booking_slot","booking_date","razorpay_order","payment_verified"]:
        st.session_state[k] = None
    st.session_state.page = "landing"
    st.rerun()

def check_session():
    return st.session_state.get("role") is not None
