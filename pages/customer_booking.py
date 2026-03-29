import streamlit as st
from datetime import date, timedelta
import urllib.parse

from utils.db import (
    get_turf_by_slug, get_bookings_for_date, create_booking,
    confirm_booking, get_blocked_dates, get_booking
)
from utils.payments import create_order, verify_payment_signature, razorpay_checkout_html
from utils.notifications import notify_booking_confirmed, notify_owner_new_booking

SLOTS = [
    "5:00 AM","6:00 AM","7:00 AM","8:00 AM","9:00 AM","10:00 AM","11:00 AM","12:00 PM",
    "1:00 PM","2:00 PM","3:00 PM","4:00 PM","5:00 PM","6:00 PM","7:00 PM","8:00 PM",
]

def show():
    # ── Topbar ────────────────────────────────────────────────────────────────
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown('<div class="brand">🏟️ TurfBook</div>', unsafe_allow_html=True)
    with c2:
        if st.button("← Back"):
            st.session_state.page = "landing"
            st.rerun()

    # ── Handle payment callback from Razorpay redirect ────────────────────────
    params = st.query_params
    payment_status = params.get("payment", "")

    if payment_status == "success":
        _handle_payment_success(params)
        return

    if payment_status == "cancelled":
        st.warning("Payment was cancelled. Your slot has NOT been reserved. Please try again.")
        st.query_params.clear()

    # ── Load turf ─────────────────────────────────────────────────────────────
    turf_slug = params.get("turf", "")
    if turf_slug:
        turf = get_turf_by_slug(turf_slug)
        if turf:
            st.session_state.turf = turf
    
    turf = st.session_state.get("turf")
    if not turf:
        _turf_selector()
        return

    st.markdown(f"### {turf['name']}")
    st.caption(f"📍 {turf.get('location','')}")
    st.markdown("---")

    # ── Customer details ──────────────────────────────────────────────────────
    if not st.session_state.cust_name:
        _customer_details_form()
        return

    st.success(f"👤 Booking as **{st.session_state.cust_name}**")

    # ── Date picker ───────────────────────────────────────────────────────────
    st.markdown("#### 📅 Select a date")
    today      = date.today()
    dates      = [today + timedelta(days=i) for i in range(7)]
    blocked    = get_blocked_dates(turf["id"])
    date_labels = []
    for d in dates:
        label = d.strftime("%a, %d %b")
        if d.isoformat() in blocked:
            label += " 🚫"
        date_labels.append(label)

    sel_label = st.radio("", date_labels, horizontal=True, label_visibility="collapsed")
    sel_date  = dates[date_labels.index(sel_label)]

    if sel_date.isoformat() in blocked:
        st.error("This date is blocked by the turf owner. Please pick another date.")
        return

    # ── Slot grid ─────────────────────────────────────────────────────────────
    st.markdown("#### ⏰ Pick a time slot")
    booked_today = [b["slot"] for b in get_bookings_for_date(turf["id"], sel_date)]

    cols = st.columns(4)
    chosen_slot = st.session_state.get("booking_slot")

    for i, slot in enumerate(SLOTS):
        with cols[i % 4]:
            is_booked = slot in booked_today
            is_sel    = slot == chosen_slot

            if is_booked:
                st.markdown(f'<div class="slot-booked">{slot}<br>🔒 Booked</div>', unsafe_allow_html=True)
            elif is_sel:
                st.markdown(f'<div class="slot-selected">✅ {slot}</div>', unsafe_allow_html=True)
                if st.button("Deselect", key=f"des_{slot}", use_container_width=True):
                    st.session_state.booking_slot = None
                    st.rerun()
            else:
                st.markdown(f'<div class="slot-available">{slot}</div>', unsafe_allow_html=True)
                if st.button("Select", key=f"sel_{slot}", use_container_width=True):
                    st.session_state.booking_slot = slot
                    st.session_state.booking_date = sel_date
                    st.rerun()

    # ── Booking summary + pay ─────────────────────────────────────────────────
    if st.session_state.booking_slot and st.session_state.booking_date == sel_date:
        st.markdown("---")
        st.markdown("#### 🧾 Booking Summary")
        st.markdown(f"""
        <div class="summary-card">
          <div class="summary-row"><span>Turf</span><span><b>{turf['name']}</b></span></div>
          <div class="summary-row"><span>Date</span><span><b>{sel_date.strftime('%A, %d %B %Y')}</b></span></div>
          <div class="summary-row"><span>Slot</span><span><b>{st.session_state.booking_slot}</b></span></div>
          <div class="summary-row summary-total"><span>Total</span><span>₹{turf['price_per_slot']}</span></div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("💳 Pay & Confirm — ₹" + str(turf["price_per_slot"]),
                     type="primary", use_container_width=True):
            _initiate_payment(turf, sel_date)


def _turf_selector():
    """Fallback when no turf slug is passed — let user enter a turf code."""
    st.markdown("#### Enter your turf booking link or code")
    st.info("Each turf has a unique URL like `turfbook.streamlit.app/?turf=greenfield`. Ask your turf owner for the link.")
    slug = st.text_input("Turf code / slug")
    if st.button("Go") and slug:
        turf = get_turf_by_slug(slug.strip().lower())
        if turf:
            st.session_state.turf = turf
            st.rerun()
        else:
            st.error("No turf found with that code.")


def _customer_details_form():
    st.markdown("#### 👤 Your details")
    with st.form("cust_form"):
        name  = st.text_input("Full name", placeholder="Rahul Sharma")
        phone = st.text_input("WhatsApp number", placeholder="98765 43210",
                              help="You'll receive booking confirmation here")
        submitted = st.form_submit_button("Continue →", type="primary", use_container_width=True)
        if submitted:
            if not name or not phone:
                st.error("Please enter both name and phone number.")
            else:
                st.session_state.cust_name  = name.strip()
                st.session_state.cust_phone = phone.strip()
                st.rerun()


def _initiate_payment(turf: dict, sel_date: date):
    try:
        order = create_order(turf["price_per_slot"], f"{turf['id']}-{sel_date.isoformat()}-{st.session_state.booking_slot}")
        booking = create_booking(
            turf_id        = turf["id"],
            customer_name  = st.session_state.cust_name,
            customer_phone = st.session_state.cust_phone,
            booking_date   = sel_date,
            slot           = st.session_state.booking_slot,
            amount         = turf["price_per_slot"],
            razorpay_order_id = order["id"],
        )
        st.session_state.razorpay_order   = order
        st.session_state.pending_booking_id = booking["id"]
        html = razorpay_checkout_html(
            order    = order,
            turf     = turf,
            customer = {"name": st.session_state.cust_name, "phone": st.session_state.cust_phone},
            amount_inr = turf["price_per_slot"],
        )
        st.components.v1.html(html, height=200)
    except Exception as e:
        st.error(f"Payment initiation failed: {e}")


def _handle_payment_success(params: dict):
    payment_id = params.get("razorpay_payment_id","")
    order_id   = params.get("razorpay_order_id","")
    signature  = params.get("razorpay_signature","")

    if not all([payment_id, order_id, signature]):
        st.error("Invalid payment response. Please contact support.")
        return

    valid = verify_payment_signature(order_id, payment_id, signature)
    if not valid:
        st.error("⚠️ Payment signature verification failed. Please contact support.")
        return

    # Confirm in DB
    booking_id = st.session_state.get("pending_booking_id")
    if booking_id:
        confirm_booking(booking_id, payment_id)
        booking = get_booking(booking_id)
        turf    = st.session_state.get("turf") or {}

        # WhatsApp notifications
        notify_booking_confirmed(
            customer_name = st.session_state.cust_name,
            phone         = st.session_state.cust_phone,
            turf_name     = turf.get("name","Turf"),
            slot          = booking["slot"],
            date_str      = booking["booking_date"],
            amount        = booking["amount"],
        )
        if turf.get("owner_phone"):
            notify_owner_new_booking(
                owner_phone   = turf["owner_phone"],
                customer_name = st.session_state.cust_name,
                slot          = booking["slot"],
                date_str      = booking["booking_date"],
                amount        = booking["amount"],
            )

    st.query_params.clear()
    st.balloons()
    st.success("🎉 Payment successful! Your slot is confirmed.")

    booking_date = st.session_state.get("booking_date")
    turf = st.session_state.get("turf", {})
    st.markdown(f"""
    <div class="summary-card">
      <div class="summary-row"><span>Turf</span><span><b>{turf.get('name','')}</b></span></div>
      <div class="summary-row"><span>Date</span><span><b>{booking_date.strftime('%A, %d %B %Y') if booking_date else ''}</b></span></div>
      <div class="summary-row"><span>Slot</span><span><b>{st.session_state.get('booking_slot','')}</b></span></div>
      <div class="summary-row"><span>Payment ID</span><span><code>{payment_id[:16]}…</code></span></div>
      <div class="summary-row summary-total"><span>Status</span><span>✅ Confirmed</span></div>
    </div>
    """, unsafe_allow_html=True)
    st.info("📲 A WhatsApp confirmation has been sent to your number.")

    if st.button("Book another slot"):
        st.session_state.booking_slot = None
        st.session_state.booking_date = None
        st.session_state.razorpay_order = None
        st.session_state.pending_booking_id = None
        st.rerun()
