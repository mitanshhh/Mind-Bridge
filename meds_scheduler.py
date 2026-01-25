import streamlit as st
import json
import google.generativeai as genai
from google_auth_oauthlib.flow import InstalledAppFlow
from datetime import datetime
from googleapiclient.discovery import build
from config.config import GOOGLE_API_KEY

st.markdown("""
<style>
.st-c3 {
    min-height: 16.25rem;
}     

#medicine-reminder-tracker{
    justify-content: center;
    display: flex;
    position: relative;
    bottom: 47px;}            
</style<>

""",unsafe_allow_html=True)

if "user_text" not in st.session_state:
    st.session_state.user_text = ""

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Medicine Tracker", layout="wide")
TIMEZONE = "Asia/Kolkata"
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# ---------------- GEMINI SETUP ----------------
genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
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
- If duration is mentioned (e.g. "for 3 days"), generate consecutive dates starting from the start date
- Convert weekdays (Mon, Tue, etc.) into actual calendar dates starting from Today
- Expand all date ranges into explicit individual dates
- Convert all times to 24-hour format
- If multiple times per day are mentioned, include all of them
- Do NOT guess missing medicines, dates, or times
- If information is missing, infer only what is logically implied by the rules above
- Return JSON only, no text, no markdown, no explanation

"""


# ---------------- GOOGLE CALENDAR ----------------
def get_calendar_service():
    flow = InstalledAppFlow.from_client_secrets_file(
        r"config\credentials.json", SCOPES
    )
    creds = flow.run_local_server(port=0)
    return build("calendar", "v3", credentials=creds)

def create_calendar_events(schedule):
    service = get_calendar_service()

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
                        "overrides": [
                            {"method": "popup", "minutes": 10}
                        ]
                    }
                }

                service.events().insert(
                    calendarId="primary",
                    body=event
                ).execute()

# ---------------- SPEECH TO TEXT ----------------


# ---------------- GEMINI CALL ----------------
def call_gemini(text):
    response = model.generate_content(
        SYSTEM_PROMPT + "\n\nUser input:\n" + text
    )
    return response.text

def parse_json(raw):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        st.error("Gemini returned invalid JSON")
        st.text(raw)
        return None

# ---------------- UI ----------------
st.title("💊 Medicine Reminder Tracker")

st.write(
    "### Enter medicine instructions using **text** or **voice**.\n\n"
    "**Example:**\n"
    "I have to take Dolo 650 for three days starting from Monday at 3 PM and 9 PM "
    "and cough syrup on Tuesday at 11 AM"
)
st.markdown("")


user_text = ""
user_text = st.text_area(
        "Medicine Instructions",
        placeholder="Type medicine schedule here..."
    )
st.session_state.user_text = user_text

st.markdown("---")
if st.button("📅 Set Medicine Reminders",key='reminder_set_btn'):
    if not st.session_state.user_text:
            st.warning("Please provide medicine instructions")
    else:
        with st.spinner("Processing..."):
            raw = call_gemini(st.session_state.user_text)
            schedule = parse_json(raw)

            if schedule:
                create_calendar_events(schedule)
                st.success("✅ All medicine reminders added to Google Calendar!")
                st.subheader("📋 Extracted Schedule")
                st.json(schedule)
