import streamlit as st
import json
import google.generativeai as genai
from datetime import datetime
from googleapiclient.discovery import build
import os 
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

load_dotenv()

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Medicine Tracker", layout="wide")
TIMEZONE = "Asia/Kolkata"
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# ---------------- GEMINI SETUP ----------------
# Ensure you have GEMINI_API_KEY in .env or st.secrets
genai.configure(api_key=os.getenv("GEMINI_API_KEY")) 

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash", # Updated to latest flash model
    generation_config={
        "temperature": 0,
        "response_mime_type": "application/json"
    }
)

todays_date_user = datetime.now().strftime("%A, %d %B %Y")

SYSTEM_PROMPT = f"""
You are a medical scheduling assistant.
Your job is to extract structured medicine reminders.
Return ONLY valid JSON in the exact format below:
{{
  "medicines": [
    {{
      "name": "string",
      "days": ["YYYY-MM-DD"],
      "times": ["HH:MM"]
    }}
  ]
}}
Rules (must follow strictly):
- Today is {todays_date_user}
- If duration is mentioned (e.g. "for 3 days"), generate consecutive dates.
- Convert weekdays into actual calendar dates starting from Today.
- Convert all times to 24-hour format.
- Return JSON only.
"""

# ---------------- OAUTH & CALENDAR FUNCTIONS ----------------

def get_oauth_flow():
    """Creates the OAuth flow object using secrets."""
    # We construct the config dictionary from st.secrets to avoid needing a local file
    client_config = {"web": st.secrets["web"]}
    
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=st.secrets["web"]["redirect_uris"][0]
    )
    return flow

def authenticate_user():
    """Handles the UI and logic for logging in."""
    if "credentials" not in st.session_state:
        st.session_state.credentials = None

    # Check if we have an auth code in the URL (returning from Google)
    if st.query_params.get("code"):
        code = st.query_params.get("code")
        flow = get_oauth_flow()
        try:
            flow.fetch_token(code=code)
            creds = flow.credentials
            st.session_state.credentials = creds.to_json()
            # Clear the query params to hide the code
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Authentication failed: {e}")

    # If already logged in, return Credentials object
    if st.session_state.credentials:
        creds_dict = json.loads(st.session_state.credentials)
        creds = Credentials.from_authorized_user_info(creds_dict, SCOPES)
        return creds
    
    return None

def create_calendar_events(schedule, creds):
    service = build("calendar", "v3", credentials=creds)

    count = 0
    for med in schedule["medicines"]:
        for day in med["days"]:
            for time in med["times"]:
                event = {
                    "summary": f"Take {med['name']}",
                    "start": {
                        "dateTime": f"{day}T{time}:00",
                        "timeZone": TIMEZONE
                    },
                    "end": {
                        "dateTime": f"{day}T{time}:30",
                        "timeZone": TIMEZONE
                    },
                    "reminders": {
                        "useDefault": False,
                        "overrides": [{"method": "popup", "minutes": 10}]
                    }
                }
                service.events().insert(calendarId="primary", body=event).execute()
                count += 1
    return count

# ---------------- GEMINI CALL ----------------
def call_gemini(text):
    response = model.generate_content(SYSTEM_PROMPT + "\n\nUser input:\n" + text)
    return response.text

def parse_json(raw):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        st.error("Gemini returned invalid JSON")
        return None

# ---------------- UI ----------------
st.title("💊 Medicine Reminder Tracker")

# 1. AUTHENTICATION SECTION
creds = authenticate_user()

if not creds:
    st.warning("Please log in to allow access to your Google Calendar.")
    flow = get_oauth_flow()
    auth_url, _ = flow.authorization_url(prompt='consent')
    st.markdown(f'<a href="{auth_url}" target="_self" style="padding:10px; background-color:#DB4437; color:white; text-decoration:none; border-radius:5px;">Login with Google</a>', unsafe_allow_html=True)
    st.stop() # Stop execution here until logged in

st.success("✅ Logged in to Google Calendar")

st.write(
    "### Enter medicine instructions\n"
    "Example: *Take Dolo 650 for three days starting Monday at 3 PM.*"
)

user_text = st.text_area("Medicine Instructions", placeholder="Type here...")

if st.button("📅 Set Medicine Reminders"):
    if not user_text:
        st.warning("Please provide instructions")
    else:
        with st.spinner("Processing with Gemini..."):
            raw = call_gemini(user_text)
            schedule = parse_json(raw)
            
            if schedule:
                st.subheader("📋 Plan")
                st.json(schedule)
                
                with st.spinner("Adding to Calendar..."):
                    try:
                        count = create_calendar_events(schedule, creds)
                        st.success(f"✅ Successfully added {count} reminders to your personal calendar!")
                    except Exception as e:
                        st.error(f"Calendar Error: {e}")