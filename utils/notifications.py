import streamlit as st
from twilio.rest import Client as TwilioClient

def get_twilio():
    return TwilioClient(
        st.secrets["TWILIO_ACCOUNT_SID"],
        st.secrets["TWILIO_AUTH_TOKEN"]
    )

def _send_whatsapp(to_phone: str, body: str):
    """Send WhatsApp message via Twilio sandbox / approved sender."""
    client = get_twilio()
    from_wa = st.secrets["TWILIO_WHATSAPP_FROM"]   # e.g. whatsapp:+14155238886
    to_wa   = f"whatsapp:+91{to_phone.replace(' ','').lstrip('0')}"
    try:
        msg = client.messages.create(body=body, from_=from_wa, to=to_wa)
        return msg.sid
    except Exception as e:
        st.warning(f"WhatsApp notification failed: {e}")
        return None

def notify_booking_confirmed(customer_name: str, phone: str,
                             turf_name: str, slot: str, date_str: str, amount: int):
    body = (
        f"✅ *Booking Confirmed!*\n\n"
        f"Hi {customer_name}, your slot is locked in 🎉\n\n"
        f"🏟️ *Turf:* {turf_name}\n"
        f"📅 *Date:* {date_str}\n"
        f"⏰ *Slot:* {slot}\n"
        f"💰 *Amount paid:* ₹{amount}\n\n"
        f"Show this message at the turf entrance. See you on the field! ⚽"
    )
    return _send_whatsapp(phone, body)

def notify_booking_cancelled(customer_name: str, phone: str,
                              turf_name: str, slot: str, date_str: str):
    body = (
        f"❌ *Booking Cancelled*\n\n"
        f"Hi {customer_name}, your booking has been cancelled.\n\n"
        f"🏟️ *Turf:* {turf_name}\n"
        f"📅 *Date:* {date_str}\n"
        f"⏰ *Slot:* {slot}\n\n"
        f"Refunds (if applicable) will be processed in 5–7 business days.\n"
        f"To rebook, visit our booking page."
    )
    return _send_whatsapp(phone, body)

def notify_owner_new_booking(owner_phone: str, customer_name: str,
                              slot: str, date_str: str, amount: int):
    body = (
        f"🆕 *New Booking Received!*\n\n"
        f"👤 *Customer:* {customer_name}\n"
        f"📅 *Date:* {date_str}\n"
        f"⏰ *Slot:* {slot}\n"
        f"💰 *Amount:* ₹{amount}\n\n"
        f"Check your TurfBook dashboard for full details."
    )
    return _send_whatsapp(owner_phone, body)
