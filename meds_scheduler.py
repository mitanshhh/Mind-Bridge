import streamlit as st
import datetime
import dateparser
import re
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Auto Med Scheduler", page_icon="💊")


REDIRECT_URI = st.secrets["web"]["redirect_uris"][0] 

SCOPES = ['https://www.googleapis.com/auth/calendar.events']

# --- AUTHENTICATION FUNCTIONS ---
def get_auth_flow():
    """Constructs the OAuth Flow from Streamlit Secrets"""
    return Flow.from_client_config(
        client_config={"web": st.secrets["web"]},
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

def authenticate_user():
    """Handles the login logic"""

    if "credentials" in st.session_state:
        return st.session_state["credentials"]

    code = st.query_params.get("code")
    
    if code:
        try:
            flow = get_auth_flow()
            flow.fetch_token(code=code)
            creds = flow.credentials
            st.session_state["credentials"] = creds
            # Clear the URL parameters to prevent re-using the code
            st.query_params.clear()
            return creds
        except Exception as e:
            st.error(f"Login failed: {e}")
            return None
            
    return None

# --- NATURAL LANGUAGE PARSER (Your "Brain") ---
def parse_and_schedule(text, service):
    """Parses text and inserts directly into Google Calendar"""
    commands = re.split(r'\n| also ', text, flags=re.IGNORECASE)
    results = []

    for cmd in commands:
        if not cmd.strip(): continue
        
        # 1. Parse details
        # (Simplified regex for demo - works for "Dolo 650 for 5 days at 4PM")
        days_match = re.search(r'(?:for|next)\s+(\d+)\s+days?', cmd, re.IGNORECASE)
        duration = int(days_match.group(1)) if days_match else 1
        
        # Extract times
        time_matches = re.findall(r'(\d{1,2}(?::\d{2})?\s?(?:am|pm|AM|PM))', cmd)
        parsed_times = [dateparser.parse(t).time() for t in time_matches]
        if not parsed_times: parsed_times = [datetime.time(9, 0)] # Default 9AM

        # Extract Name
        clean_name = cmd.split(" at ")[0].split(" for ")[0].replace("Take", "").strip()

        # 2. Loop and Insert into Calendar
        today = datetime.datetime.now().date()
        
        for day_offset in range(duration):
            target_date = today + datetime.timedelta(days=day_offset)
            
            for time_obj in parsed_times:
                # Combine date + time
                start_dt = datetime.datetime.combine(target_date, time_obj)
                end_dt = start_dt + datetime.timedelta(minutes=30)
                
                event = {
                    'summary': f'💊 Take {clean_name}',
                    'description': f'Generated from command: {cmd}',
                    'start': {
                        'dateTime': start_dt.isoformat(),
                        'timeZone': 'Asia/Kolkata', 
                    },
                    'end': {
                        'dateTime': end_dt.isoformat(),
                        'timeZone': 'Asia/Kolkata',
                    },
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'popup', 'minutes': 10},
                            {'method': 'popup', 'minutes': 0},
                        ],
                    },
                }
                
                # API CALL
                created_event = service.events().insert(calendarId='primary', body=event).execute()
                results.append(f"Set: {clean_name} on {target_date} at {time_obj}")

    return results

# --- UI LOGIC ---
st.title("💊 Medicines Scheduler")

creds = authenticate_user()

if not creds:
    st.warning("Please log in to allow this app to access your Calendar.")
    flow = get_auth_flow()
    auth_url, _ = flow.authorization_url(prompt='consent')
    
    # Show the Login Button
    st.link_button("🔐 Login with Google", auth_url)

else:
    st.success("✅ Authenticated with Google!")
    
    # Initialize the API Service
    service = build('calendar', 'v3', credentials=creds)

    st.subheader("Tell me your schedule")
    user_input = st.text_area("Example: Take Dolo for 3 days at 2PM and 8PM")
    
    if st.button("🚀 Schedule It Automatically"):
        if user_input:
            with st.spinner("Talking to Google..."):
                try:
                    logs = parse_and_schedule(user_input, service)
                    st.success("Done! Added the following to your calendar:")
                    for log in logs:
                        st.write(f"- {log}")
                except Exception as e:
                    st.error(f"An error occurred: {e}")