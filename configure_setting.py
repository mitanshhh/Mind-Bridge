import streamlit as st
import sqlite3
import time
from Auth.auth import onboarding_popup


# ---------- CONFIG ----------
DB_FILE = r"Database\user_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT,
            phone TEXT,
            address TEXT
        )
    """)
    conn.commit()
    conn.close()


# ---------- DB HELPERS ----------
def get_user(email):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "SELECT name, phone, email, address FROM users WHERE email=?",
        (email,)
    )
    user = c.fetchone()
    conn.close()
    return user  


def update_user(old_email, name, phone, new_email, address):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        UPDATE users
        SET name=?, phone=?, email=?, address=?
        WHERE email=?
    """, (name, phone, new_email, address, old_email))

    conn.commit()
    conn.close()

# ---------- COOKIE MANAGER ----------
from streamlit_cookies_manager import EncryptedCookieManager
cookies = EncryptedCookieManager(prefix="myapp/", password="pym1t-mh26")
if not cookies.ready():
    st.stop()


# ---------- AUTH RESOLUTION ----------
if "user_email" not in st.session_state:
    cookie_email = cookies.get("user_email")
    if cookie_email:
        st.session_state.user_email = cookie_email
    else:
        onboarding_popup(cookies)
        st.stop()

init_db()
# ---------- LOAD USER ----------
user = get_user(st.session_state.user_email)
if not user:
    onboarding_popup(cookies)
    st.stop()


name, phone, email, address = user

# ---------- UI ----------
st.title("⚙️ Account Settings")
st.caption("Edit your personal information securely")

with st.form("settings_form"):
    new_name = st.text_input("Full Name", value=name)
    new_phone = st.text_input("Phone Number", value=phone)
    new_email = st.text_input("Email ID", value=email)
    new_address = st.text_area("Address", value=address)

    submitted = st.form_submit_button("💾 Save Changes")

    if submitted:
        if not new_name or not new_email:
            st.warning("Name and Email cannot be empty.")
        else:
            update_user(
                old_email=email,
                name=new_name,
                phone=new_phone,
                new_email=new_email,
                address=new_address
            )

            # Sync session + cookies
            st.session_state.user_email = new_email
            st.session_state.user_name = new_name
            cookies["user_email"] = new_email
            cookies["user_name"] = new_name
            cookies.save()

            st.success("Profile updated successfully ✅")
            time.sleep(5)
            st.rerun()
