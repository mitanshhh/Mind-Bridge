import streamlit as st
import sqlite3

DB_FILE = r"Database\user_data.db"

def save_user_to_db(name, phone, email, address):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO users (email, name, phone, address)
        VALUES (?, ?, ?, ?)
    """, (email, name, phone, address))
    conn.commit()
    conn.close()

@st.dialog("Welcome! Please enter your details")
def onboarding_popup(cookies):
    st.write("We need a few details to personalize your experience.")

    with st.form("onboarding_form"):
        name = st.text_input("Full Name")
        phone = st.text_input("Phone Number")
        email = st.text_input("Email ID")
        address = st.text_area("Address")

        submitted = st.form_submit_button("Save & Continue")

        if submitted:
            if not name or not email:
                st.warning("Name and Email are required.")
                return

            save_user_to_db(name, phone, email, address)

            st.session_state.user_email = email
            st.session_state.user_name = name

            cookies["user_email"] = email
            cookies["user_name"] = name
            cookies.save()

            st.rerun()
