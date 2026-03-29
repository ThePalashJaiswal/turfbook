import streamlit as st
import razorpay
import hmac, hashlib

def get_razorpay_client():
    return razorpay.Client(
        auth=(st.secrets["RAZORPAY_KEY_ID"], st.secrets["RAZORPAY_KEY_SECRET"])
    )

def create_order(amount_inr: int, booking_ref: str) -> dict:
    client = get_razorpay_client()
    order = client.order.create({
        "amount":   amount_inr * 100,
        "currency": "INR",
        "receipt":  booking_ref[:40],
        "notes":    {"booking_ref": booking_ref[:40]},
    })
    return order

def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    key_secret = st.secrets["RAZORPAY_KEY_SECRET"]
    msg = f"{order_id}|{payment_id}"
    gen_sig = hmac.new(key_secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(gen_sig, signature)

def razorpay_checkout_html(order: dict, turf: dict, customer: dict, amount_inr: int) -> str:
    key_id = st.secrets["RAZORPAY_KEY_ID"]
    return f"""
    <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
    <script>
    window.onload = function() {{
        var options = {{
            key:         "{key_id}",
            amount:      "{amount_inr * 100}",
            currency:    "INR",
            name:        "{turf['name']}",
            description: "Turf slot booking",
            order_id:    "{order['id']}",
            prefill: {{
                name:    "{customer['name']}",
                contact: "{customer['phone']}",
            }},
            theme: {{ color: "#1D9E75" }},
            handler: function(response) {{
                var url = window.location.pathname
                    + "?payment=success"
                    + "&razorpay_payment_id=" + response.razorpay_payment_id
                    + "&razorpay_order_id="   + response.razorpay_order_id
                    + "&razorpay_signature="  + response.razorpay_signature;
                window.location.href = url;
            }},
            modal: {{
                ondismiss: function() {{
                    window.location.href = window.location.pathname + "?payment=cancelled";
                }}
            }}
        }};
        var rzp = new Razorpay(options);
        rzp.open();
    }};
    </script>
    <div style="text-align:center;padding:40px;font-family:sans-serif">
        <p style="color:#555">Opening payment window...</p>
    </div>
    """
