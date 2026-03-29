from datetime import date, datetime
import streamlit as st
from utils.supabase_client import get_supabase

# ── Turfs ─────────────────────────────────────────────────────────────────────

def get_turf(turf_id: str) -> dict | None:
    sb  = get_supabase()
    res = sb.table("turfs").select("*").eq("id", turf_id).single().execute()
    return res.data

def get_turf_by_slug(slug: str) -> dict | None:
    sb  = get_supabase()
    res = sb.table("turfs").select("*").eq("slug", slug).single().execute()
    return res.data

def get_turfs_by_owner(owner_id: str) -> list[dict]:
    sb  = get_supabase()
    res = sb.table("turfs").select("*").eq("owner_id", owner_id).execute()
    return res.data or []

def update_turf(turf_id: str, data: dict):
    sb = get_supabase()
    sb.table("turfs").update(data).eq("id", turf_id).execute()

# ── Bookings ──────────────────────────────────────────────────────────────────

def get_bookings_for_date(turf_id: str, booking_date: date) -> list[dict]:
    sb  = get_supabase()
    res = (sb.table("bookings")
             .select("*")
             .eq("turf_id", turf_id)
             .eq("booking_date", booking_date.isoformat())
             .neq("status", "cancelled")
             .execute())
    return res.data or []

def get_bookings_for_turf(turf_id: str, limit: int = 100) -> list[dict]:
    sb  = get_supabase()
    res = (sb.table("bookings")
             .select("*")
             .eq("turf_id", turf_id)
             .order("created_at", desc=True)
             .limit(limit)
             .execute())
    return res.data or []

def get_bookings_range(turf_id: str, from_date: date, to_date: date) -> list[dict]:
    sb  = get_supabase()
    res = (sb.table("bookings")
             .select("*")
             .eq("turf_id", turf_id)
             .gte("booking_date", from_date.isoformat())
             .lte("booking_date", to_date.isoformat())
             .neq("status", "cancelled")
             .execute())
    return res.data or []

def create_booking(turf_id: str, customer_name: str, customer_phone: str,
                   booking_date: date, slot: str, amount: int,
                   razorpay_order_id: str) -> dict:
    sb  = get_supabase()
    res = sb.table("bookings").insert({
        "turf_id":          turf_id,
        "customer_name":    customer_name,
        "customer_phone":   customer_phone,
        "booking_date":     booking_date.isoformat(),
        "slot":             slot,
        "amount":           amount,
        "status":           "pending_payment",
        "razorpay_order_id": razorpay_order_id,
    }).execute()
    return res.data[0]

def confirm_booking(booking_id: str, razorpay_payment_id: str):
    sb = get_supabase()
    sb.table("bookings").update({
        "status":               "confirmed",
        "razorpay_payment_id":  razorpay_payment_id,
        "paid_at":              datetime.utcnow().isoformat(),
    }).eq("id", booking_id).execute()

def cancel_booking(booking_id: str):
    sb = get_supabase()
    sb.table("bookings").update({"status": "cancelled"}).eq("id", booking_id).execute()

def get_booking(booking_id: str) -> dict | None:
    sb  = get_supabase()
    res = sb.table("bookings").select("*").eq("id", booking_id).single().execute()
    return res.data

# ── Analytics ─────────────────────────────────────────────────────────────────

def analytics_summary(turf_id: str) -> dict:
    """Returns aggregated analytics for the owner dashboard."""
    from datetime import timedelta
    sb    = get_supabase()
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    all_bks = get_bookings_for_turf(turf_id, limit=1000)
    confirmed = [b for b in all_bks if b["status"] == "confirmed"]

    today_bks = [b for b in confirmed if b["booking_date"] == today.isoformat()]
    week_bks  = [b for b in confirmed if b["booking_date"] >= week_start.isoformat()]

    total_revenue = sum(b["amount"] for b in confirmed)
    today_revenue = sum(b["amount"] for b in today_bks)
    week_revenue  = sum(b["amount"] for b in week_bks)

    # occupancy for last 7 days (booked / total available slots per day)
    total_slots = 16  # 5AM–9PM, 1hr each
    days_7 = [today - timedelta(days=i) for i in range(6, -1, -1)]
    occ_data = []
    for d in days_7:
        day_bks = [b for b in confirmed if b["booking_date"] == d.isoformat()]
        occ_data.append({
            "date":    d.strftime("%d %b"),
            "booked":  len(day_bks),
            "revenue": sum(b["amount"] for b in day_bks),
        })

    return {
        "total_bookings":  len(confirmed),
        "total_revenue":   total_revenue,
        "today_bookings":  len(today_bks),
        "today_revenue":   today_revenue,
        "week_bookings":   len(week_bks),
        "week_revenue":    week_revenue,
        "occupancy_data":  occ_data,
        "all_confirmed":   confirmed,
    }

# ── Blocked dates ─────────────────────────────────────────────────────────────

def get_blocked_dates(turf_id: str) -> list[str]:
    sb  = get_supabase()
    res = sb.table("blocked_dates").select("date").eq("turf_id", turf_id).execute()
    return [r["date"] for r in (res.data or [])]

def block_date(turf_id: str, d: date):
    sb = get_supabase()
    sb.table("blocked_dates").upsert({"turf_id": turf_id, "date": d.isoformat()}).execute()

def unblock_date(turf_id: str, d: date):
    sb = get_supabase()
    sb.table("blocked_dates").delete().eq("turf_id", turf_id).eq("date", d.isoformat()).execute()
