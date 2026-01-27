import streamlit as st
import sqlite3
import time
from Auth.auth import onboarding_popup
import os

if "USER_GEMINI_API_KEY" not in st.session_state:
    st.session_state["USER_GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")

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

st.markdown("---")
# ================= API KEY SECTION =================
st.header("🔑 Gemini API Setup")

st.info("To use the AI features, you need a Google Gemini API Key.")

# Instructions
with st.expander("📝 **How to get your API Key (Step-by-Step)**", expanded=True):
    st.markdown("""
    1. Go to **[Google AI Studio](https://aistudio.google.com/app/apikey)**.
    2. Log in with your Google Account.
    3. Click on the blue **"Create API key"** button.
    4. Select "Create key in new project" (or an existing one).
    5. **Copy** the generated key string (it starts with `AIza...`).
    6. Paste it in the box below and click **Save**.
    """)


current_key = st.session_state["USER_GEMINI_API_KEY"]
masked_key = f"{current_key[:4]}...{current_key[-4:]}" if len(current_key) > 8 else "Not Set"

col1, col2 = st.columns([3, 1])
with col1:
    api_key_input = st.text_input(
        "Enter API Key",
        value=current_key,
        type="password",
        placeholder="AIzaSy...",
        help="This key is stored only in your current browser session for privacy."
    )

if st.button("💾 Save API Key", type="primary"):
    if len(api_key_input) < 30 and len(api_key_input) > 0:
        st.error("Invalid API Key format. It should be longer.")
    else:

        st.session_state["USER_GEMINI_API_KEY"] = api_key_input.strip()
        

        os.environ["GEMINI_API_KEY"] = api_key_input.strip()
        
        st.success("✅ API Key applied to this session!")
        st.rerun()

# Show current status
if st.session_state["USER_GEMINI_API_KEY"]:
    st.caption(f"✅ Active Key for this session: `{masked_key}`")
else:
    st.caption("❌ No API Key found for this session.")

st.markdown("---")

with st.expander("About the Developers"):
    st.write("Want to connect with the people behind this project?")

    developers = [
        ("Mitansh Jadhav", "Backend, RAG & UI", "https://www.linkedin.com/in/mitanshjadhav/"),
        ("Safa Sayed", "Backend for Therapist Finder", "https://www.linkedin.com/in/sayed-safa/"),
        ("Om Koramble", "SOS, Prompt Engineering & APIs", "https://www.linkedin.com/in/om-korade-475279398/"),
        ("Nupur Ogale", "Backend for Medicine Scheduler", "https://www.linkedin.com/in/nupur-ogale-88aa46395/"),
    ]

    cols = st.columns(4)

    for col, dev in zip(cols, developers):
        with col:
            st.markdown(f"### {dev[0]}")
            st.caption(dev[1])
            st.link_button("LinkedIn", dev[2])
