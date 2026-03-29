# 🏟️ TurfBook — SaaS Turf Booking Platform

A white-label turf booking SaaS built with **Streamlit + Supabase + Razorpay + Twilio WhatsApp**.

Each turf owner gets their own booking link: `yourapp.streamlit.app/?turf=greenfield`

---

## ✨ Features

- **Customer portal** — Date + slot selection, real-time availability, Razorpay payment
- **Owner dashboard** — Bookings view, analytics, slot management, date blocking
- **WhatsApp notifications** — Customers & owners get instant booking confirmations
- **Analytics** — Revenue charts, popular slots, day-by-day occupancy
- **White-label** — Each turf has a unique slug/URL, own name & pricing

---

## 🗂️ Project Structure

```
turfbook/
├── app.py                        # Main entry + router
├── requirements.txt
├── supabase_schema.sql           # Run this in Supabase SQL Editor
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example      # Copy to secrets.toml and fill in
├── pages/
│   ├── landing.py
│   ├── customer_booking.py
│   ├── owner_login.py
│   └── owner_dashboard.py
└── utils/
    ├── supabase_client.py
    ├── auth.py
    ├── db.py
    ├── payments.py
    └── notifications.py
```

---

## 🚀 Deployment — Step by Step

### Step 1 — Set up Supabase (free)

1. Go to [supabase.com](https://supabase.com) → New project
2. Once created, go to **SQL Editor → New query**
3. Paste the contents of `supabase_schema.sql` and click **Run**
4. Go to **Project Settings → API** and copy:
   - `Project URL` → `SUPABASE_URL`
   - `anon public` key → `SUPABASE_KEY`

### Step 2 — Set up Razorpay

1. Create account at [razorpay.com](https://razorpay.com)
2. Go to **Settings → API Keys → Generate Key**
3. Copy `Key ID` → `RAZORPAY_KEY_ID`
4. Copy `Key Secret` → `RAZORPAY_KEY_SECRET`
5. For testing, use test mode keys (prefix `rzp_test_`)

### Step 3 — Set up Twilio WhatsApp

1. Create account at [twilio.com](https://twilio.com)
2. Go to **Messaging → Try it out → Send a WhatsApp message**
3. Follow sandbox setup (customers send a join message once)
4. Copy `Account SID` → `TWILIO_ACCOUNT_SID`
5. Copy `Auth Token` → `TWILIO_AUTH_TOKEN`
6. Sandbox number (e.g. `whatsapp:+14155238886`) → `TWILIO_WHATSAPP_FROM`

> For production: apply for a Twilio WhatsApp Business sender (~2 weeks approval)

### Step 4 — Deploy to Streamlit Cloud (free)

1. Push this repo to **GitHub** (keep `secrets.toml` in `.gitignore` — it's already there)
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Select your repo, branch `main`, main file `app.py`
4. Go to **Advanced settings → Secrets** and paste:

```toml
SUPABASE_URL            = "https://xxxx.supabase.co"
SUPABASE_KEY            = "your-anon-key"
RAZORPAY_KEY_ID         = "rzp_live_xxxx"
RAZORPAY_KEY_SECRET     = "your-secret"
TWILIO_ACCOUNT_SID      = "ACxxxx"
TWILIO_AUTH_TOKEN       = "xxxx"
TWILIO_WHATSAPP_FROM    = "whatsapp:+14155238886"
APP_URL                 = "https://yourapp.streamlit.app"
```

5. Click **Deploy** — live in ~60 seconds.

---

## 🏪 Onboarding a New Turf Owner

1. In Supabase → **Table Editor → owners**: insert a new row with email + bcrypt password hash
2. In **turfs**: insert a row with `owner_id`, `name`, unique `slug`, `price_per_slot`
3. Share the owner login link + their booking URL: `yourapp.streamlit.app/?turf=SLUG`

### Generate a password hash (Python):
```python
import bcrypt
hash = bcrypt.hashpw("their_password".encode(), bcrypt.gensalt()).decode()
print(hash)  # paste this into owners.password_hash
```

---

## 💰 Monetisation Ideas

- Charge ₹500–2000/month per turf (SaaS subscription)
- Take 1–2% transaction fee on each booking
- Upsell: custom domain, SMS instead of WhatsApp sandbox, priority support

---

## 🔧 Customising Per Turf

Each turf's name, location, pricing, and description is configurable from the **owner dashboard → Settings tab** — no code changes needed.

---

## 📞 Support

Built by TurfBook. For onboarding new turf owners or technical issues, contact your admin.
