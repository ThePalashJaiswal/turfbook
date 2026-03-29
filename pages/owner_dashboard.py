import streamlit as st
import pandas as pd
from datetime import date, timedelta

from utils.auth import logout
from utils.db import (
    analytics_summary, get_bookings_for_date, get_bookings_for_turf,
    cancel_booking, get_blocked_dates, block_date, unblock_date, update_turf
)
from utils.notifications import notify_booking_cancelled

def show():
    if not st.session_state.get("turf"):
        st.warning("Session expired. Please login again.")
        logout()
        return

    turf = st.session_state.turf

    # ── Topbar ────────────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns([3, 2, 1])
    with c1:
        st.markdown(f'<div class="brand">🏟️ {turf["name"]}</div>', unsafe_allow_html=True)
        st.caption(f"📍 {turf.get('location','')} · Owner Dashboard")
    with c2:
        app_url = st.secrets.get("APP_URL", "")
        booking_link = f"{app_url}/?turf={turf['slug']}"
        st.markdown(f"**Booking link:**")
        st.code(booking_link, language=None)
    with c3:
        if st.button("🚪 Logout", use_container_width=True):
            logout()

    st.markdown("---")

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Analytics", "📋 Bookings", "🗓️ Manage Slots", "⚙️ Settings"])

    with tab1:
        _analytics_tab(turf)

    with tab2:
        _bookings_tab(turf)

    with tab3:
        _slots_tab(turf)

    with tab4:
        _settings_tab(turf)


# ── Analytics tab ─────────────────────────────────────────────────────────────

def _analytics_tab(turf: dict):
    data = analytics_summary(turf["id"])

    st.markdown("#### 📊 Performance Overview")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Today's Revenue",  f"₹{data['today_revenue']}",  f"{data['today_bookings']} bookings")
    m2.metric("This Week",        f"₹{data['week_revenue']}",   f"{data['week_bookings']} bookings")
    m3.metric("All-time Revenue", f"₹{data['total_revenue']}")
    m4.metric("Total Bookings",   data["total_bookings"])

    st.markdown("---")
    st.markdown("#### 📈 Last 7 Days — Bookings & Revenue")

    occ = data["occupancy_data"]
    if occ:
        df = pd.DataFrame(occ)
        col1, col2 = st.columns(2)
        with col1:
            st.bar_chart(df.set_index("date")["booked"], use_container_width=True, height=220)
            st.caption("Bookings per day")
        with col2:
            st.bar_chart(df.set_index("date")["revenue"], use_container_width=True, height=220)
            st.caption("Revenue per day (₹)")

    st.markdown("---")
    st.markdown("#### 🕐 Most popular slots")
    confirmed = data["all_confirmed"]
    if confirmed:
        slot_counts = pd.Series([b["slot"] for b in confirmed]).value_counts().reset_index()
        slot_counts.columns = ["Slot", "Bookings"]
        st.dataframe(slot_counts, use_container_width=True, hide_index=True)
    else:
        st.info("No bookings yet to analyse.")


# ── Bookings tab ──────────────────────────────────────────────────────────────

def _bookings_tab(turf: dict):
    st.markdown("#### 📋 Bookings")

    col1, col2 = st.columns([2, 1])
    with col1:
        view_mode = st.radio("View", ["Today", "Specific date", "All recent"], horizontal=True)
    with col2:
        show_cancelled = st.checkbox("Show cancelled", value=False)

    today = date.today()

    if view_mode == "Today":
        bookings = get_bookings_for_date(turf["id"], today)
        if show_cancelled:
            all_bks = get_bookings_for_turf(turf["id"])
            bookings = [b for b in all_bks if b["booking_date"] == today.isoformat()]
        st.caption(f"Showing bookings for {today.strftime('%A, %d %B %Y')}")

    elif view_mode == "Specific date":
        pick = st.date_input("Select date", value=today)
        bookings = get_bookings_for_date(turf["id"], pick)
        if show_cancelled:
            all_bks = get_bookings_for_turf(turf["id"])
            bookings = [b for b in all_bks if b["booking_date"] == pick.isoformat()]
        st.caption(f"Showing bookings for {pick.strftime('%A, %d %B %Y')}")

    else:
        bookings = get_bookings_for_turf(turf["id"], limit=50)
        if not show_cancelled:
            bookings = [b for b in bookings if b["status"] != "cancelled"]

    if not bookings:
        st.info("No bookings found for the selected filter.")
        return

    # Export
    df_export = pd.DataFrame([{
        "Name":    b["customer_name"],
        "Phone":   b["customer_phone"],
        "Date":    b["booking_date"],
        "Slot":    b["slot"],
        "Amount":  b["amount"],
        "Status":  b["status"],
    } for b in bookings])
    st.download_button("⬇️ Export CSV", df_export.to_csv(index=False),
                       "bookings.csv", "text/csv", use_container_width=False)

    st.markdown("<br>", unsafe_allow_html=True)

    for b in bookings:
        status_badge = {
            "confirmed":       '<span class="badge-green">✅ confirmed</span>',
            "pending_payment": '<span class="badge-amber">⏳ pending</span>',
            "cancelled":       '<span class="badge-red">❌ cancelled</span>',
        }.get(b["status"], b["status"])

        with st.container():
            c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
            with c1:
                st.markdown(f"**{b['customer_name']}** · {b['customer_phone']}")
                st.caption(f"{b['booking_date']} · {b['slot']}")
            with c2:
                st.markdown(status_badge, unsafe_allow_html=True)
            with c3:
                st.markdown(f"**₹{b['amount']}**")
            with c4:
                if b["status"] == "confirmed":
                    if st.button("Cancel", key=f"cancel_{b['id']}"):
                        cancel_booking(b["id"])
                        notify_booking_cancelled(
                            customer_name = b["customer_name"],
                            phone         = b["customer_phone"],
                            turf_name     = turf["name"],
                            slot          = b["slot"],
                            date_str      = b["booking_date"],
                        )
                        st.success("Booking cancelled and customer notified.")
                        st.rerun()
            st.markdown('<hr style="margin:6px 0;opacity:0.2">', unsafe_allow_html=True)


# ── Slots tab ─────────────────────────────────────────────────────────────────

def _slots_tab(turf: dict):
    st.markdown("#### 🗓️ Slot Availability & Date Blocking")
    today   = date.today()
    blocked = get_blocked_dates(turf["id"])

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**View availability for a date**")
        pick = st.date_input("Date", value=today, key="slot_date_pick")
        if pick.isoformat() in blocked:
            st.error("🚫 This date is blocked. No bookings possible.")
        else:
            from utils.db import get_bookings_for_date
            booked_slots = [b["slot"] for b in get_bookings_for_date(turf["id"], pick)]
            SLOTS = [
                "5:00 AM","6:00 AM","7:00 AM","8:00 AM","9:00 AM","10:00 AM",
                "11:00 AM","12:00 PM","1:00 PM","2:00 PM","3:00 PM","4:00 PM",
                "5:00 PM","6:00 PM","7:00 PM","8:00 PM",
            ]
            cols = st.columns(4)
            for i, s in enumerate(SLOTS):
                with cols[i % 4]:
                    if s in booked_slots:
                        st.markdown(f'<div class="slot-booked">{s}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="slot-available">{s}</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("**Block / unblock dates**")
        st.caption("Blocked dates are hidden from customers.")
        block_pick = st.date_input("Select date to block/unblock", value=today + timedelta(days=1), key="block_date_pick")

        is_blocked = block_pick.isoformat() in blocked
        if is_blocked:
            st.warning(f"{block_pick.strftime('%d %b %Y')} is currently BLOCKED")
            if st.button("✅ Unblock this date", use_container_width=True):
                unblock_date(turf["id"], block_pick)
                st.success("Date unblocked.")
                st.rerun()
        else:
            st.success(f"{block_pick.strftime('%d %b %Y')} is currently OPEN")
            if st.button("🚫 Block this date", use_container_width=True):
                block_date(turf["id"], block_pick)
                st.warning("Date blocked. No new bookings will be accepted.")
                st.rerun()

        if blocked:
            st.markdown("**Currently blocked dates:**")
            for d in sorted(blocked):
                st.markdown(f"- {d}")


# ── Settings tab ──────────────────────────────────────────────────────────────

def _settings_tab(turf: dict):
    st.markdown("#### ⚙️ Turf Settings")
    st.caption("Changes are saved immediately.")

    with st.form("turf_settings"):
        name     = st.text_input("Turf name",      value=turf.get("name",""))
        location = st.text_input("Location",        value=turf.get("location",""))
        price    = st.number_input("Price per slot (₹)", value=int(turf.get("price_per_slot", 800)), step=50)
        phone    = st.text_input("Owner WhatsApp number (for new booking alerts)",
                                 value=turf.get("owner_phone",""),
                                 placeholder="98765 43210")
        desc     = st.text_area("Short description (shown to customers)",
                                value=turf.get("description",""), height=80)
        saved    = st.form_submit_button("💾 Save changes", type="primary")

    if saved:
        update_turf(turf["id"], {
            "name":           name,
            "location":       location,
            "price_per_slot": price,
            "owner_phone":    phone,
            "description":    desc,
        })
        st.session_state.turf["name"]           = name
        st.session_state.turf["location"]       = location
        st.session_state.turf["price_per_slot"] = price
        st.session_state.turf["owner_phone"]    = phone
        st.session_state.turf["description"]    = desc
        st.success("Settings saved!")

    st.markdown("---")
    st.markdown("#### 📎 Your booking link")
    app_url = st.secrets.get("APP_URL","https://yourapp.streamlit.app")
    link    = f"{app_url}/?turf={turf['slug']}"
    st.code(link)
    st.caption("Share this link with your customers. They'll land directly on your turf's booking page.")

    st.markdown("#### 🔐 Change password")
    st.info("Password changes: go to Supabase → Table Editor → owners → update `password_hash` using the `hash_password()` utility, or contact your TurfBook admin.")
