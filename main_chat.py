import streamlit as st
import sqlite3
from rag_agent import ask_ai
from twilio_call_backend import call_emergency

# Custom CSS (Restored exact user version with button fix)
st.markdown("""
<style>
    /* Force a dark theme look if not already set by system */
    [data-testid="stAppViewContainer"] {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    /* Ensure main block uses full width */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
        max-width: 100% !important;
    }

    /* --- FIXED HEADER STYLING --- */
    
    .block-container > [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"]:has(div.fixed-header-marker) {
        position: fixed;
        top: 3.5rem; /* Height of the standard Streamlit nav bar */
        left: 0;
        right: 0;
        z-index: 999;
        background-color: #0e1117;
        padding: 1rem 5rem;
        border-bottom: 1px solid #262730;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        height: auto; 
    }
    
    .header-text {
        font-size: 30px;
        font-weight: bold;
        color: #e0e0e0;
        left: 3px;
        position: relative;
        top: 34px;
        z-index: 1; /* Lower z-index than button */
    }
    
    /* NEW: Fix button clickability by raising it above the text container */
    div[data-testid="stVerticalBlock"]:has(div.fixed-header-marker) button {
        position: relative;
        z-index: 1000;
    }
    
    /* Spacer to push chat content down below the fixed header */
    .header-spacer {
        height: 130px; 
    }
    
    /* --- ZIG-ZAG CHAT STYLING --- */
    
    [data-testid="stChatMessage"] {
        padding: 1rem;
        margin-bottom: 0.5rem;
    }

    /* Bot (Odd) - Left Aligned */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #1c1e24;
        border-radius: 10px;
    }
    
    /* User (Even) - Right Aligned */
    [data-testid="stChatMessage"]:nth-child(even) {
        flex-direction: row-reverse;
        background-color: #262730;
        border-radius: 10px;
    }
    
    /* Reduce vertical gaps */
    div[data-testid="stVerticalBlock"] {
        gap: 0.5rem;
    }

    /* --- CHAT INPUT STYLING --- */
    
    .stChatInput {
        position: fixed;
        left: 31px;
        right: 0;
        width: 94%;
        padding: 1rem 3rem 1rem 3rem;
        background-color: #0e1117;
        z-index: 1000;
        box-shadow: 0 -4px 6px -1px rgba(0, 0, 0, 0.1);
        bottom: 25px;
    }
    
    .content-spacer {
        height: 17px;
    }
    
            
    #your-journey-to-a-healthier-mind-begins-here{
        position: relative;
        left: 3px;
        bottom: 104px;
        font-size: 18px;
    }
    
    .st-emotion-cache-8atqhb{
        width: 33%;
        position: relative;
        left: 222px;
        top:54px
    }

    .stFormSubmitButton{
        width: 100%;
        position: relative;
        left: 146px;
        top: 5px;
    }
    
@media (max-width: 768px){
    .stChatInput {
    position: fixed;
    left: -19px;
    right: 0;
    width: 110%;
    padding: 1rem 3rem 1rem 3rem;
    background-color: #0e1117;
    z-index: 1000;
    box-shadow: 0 -4px 6px -1px rgba(0, 0, 0, 0.1);
    bottom: 45px;
}
.st-emotion-cache-8atqhb {
    width: 33%;
    position: relative;
    left: 244px;
    top: -10px;
}
#your-journey-to-a-healthier-mind-begins-here {
    position: relative;
    left: 3px;
    bottom: 124px;
    font-size: 18px;
}
}

</style>

""", unsafe_allow_html=True)

if "is_generating" not in st.session_state:
    st.session_state.is_generating = False


# --- Database Management (SQLite) ---
DB_FILE = r"Database\user_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (email TEXT PRIMARY KEY, name TEXT, phone TEXT, address TEXT)''')
    conn.commit()
    conn.close()

def save_user_to_db(name, phone, email, address):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT OR REPLACE INTO users (email, name, phone, address) VALUES (?, ?, ?, ?)",
                  (email, name, phone, address))
        conn.commit()
    except Exception as e:
        st.error(f"Error saving to DB: {e}")
    finally:
        conn.close()

def get_user_from_db(email):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=?", (email,))
    user = c.fetchone()
    conn.close()
    return user

# --- Cookie Management Wrapper ---
try:
    from streamlit_cookies_manager import EncryptedCookieManager
    cookies = EncryptedCookieManager(prefix="myapp/", password="pym1t-mh26")
    if not cookies.ready():
        st.stop()
    HAS_COOKIES = True
except ImportError:
    HAS_COOKIES = False
    class MockCookies:
        def __init__(self): self._data = {}
        def get(self, key): return st.session_state.get(f"cookie_{key}", None)
        def __setitem__(self, key, value): st.session_state[f"cookie_{key}"] = value
        def save(self): pass
    cookies = MockCookies()

# --- Helper Functions ---


def clear_chat():
    st.session_state.messages = []

# --- Components ---

@st.dialog("Welcome! Please enter your details")
def onboarding_popup():
    st.write("We need a few details to personalize your experience.")
    with st.form("onboarding_form"):
        name = st.text_input("Full Name")
        phone = st.text_input("Phone Number")
        email = st.text_input("Email ID")
        address = st.text_area("Address")
        
        submitted = st.form_submit_button("Save & Continue")
        
        if submitted:
            if name and email:
                save_user_to_db(name, phone, email, address)
                cookies['user_email'] = email
                cookies['user_name'] = name
                cookies.save()
                st.session_state['user_name'] = name
                st.session_state['user_email'] = email
                st.rerun()
            else:
                st.warning("Please fill in at least Name and Email.")

def render_header():
    """Renders the top section with Name, SOS, and Health Tip."""
    user_name = st.session_state.get('user_name', 'Guest')
    
    # We create a container. The CSS looks for a container WITH the marker inside it.
    with st.container():
        # Marker is NOW INSIDE the container
        st.markdown('<div class="fixed-header-marker"></div>', unsafe_allow_html=True)
        
        # Changed to [4, 1] to push button to the right
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"<div class='header-text'>Hey, {user_name} 👋</div>", unsafe_allow_html=True)
            
        with col2:
            # Added callback to make it functional
            st.button("Clear Chat", key="clear_chat_button",use_container_width=True, on_click=clear_chat)

# --- Page Logic ---

def main():
    init_db()
    
    # --- Onboarding Logic ---
    if 'user_email' not in st.session_state:
        cookie_email = cookies.get('user_email')
        if cookie_email:
            user_data = get_user_from_db(cookie_email)
            if user_data:
                st.session_state['user_email'] = user_data[0]
                st.session_state['user_name'] = user_data[1]
            else:
                onboarding_popup()
        else:
            onboarding_popup()

    # --- Header Render ---
    render_header()
    
    # Add a spacer so the fixed header doesn't cover the first messages
    st.markdown('<div class="header-spacer"></div>', unsafe_allow_html=True)
    
    st.subheader("Your journey to a healthier mind begins here.")
    
    # --- Chat Interface ---
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Wrapper for chat messages
    with st.container():
        if not st.session_state.is_generating:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])


    # Spacer to ensure the last message isn't hidden by the fixed input
    st.markdown("<div class='content-spacer'></div>", unsafe_allow_html=True)

    # ---- CHAT INPUT ----
    if "chat_input_value" not in st.session_state:
        st.session_state.chat_input_value = ""

    user_query = st.chat_input("What is on your mind?")

    if user_query:
        st.session_state.chat_input_value = ""
        st.session_state.is_generating = True   # 🔴 lock UI

        with st.chat_message("user"):
            st.markdown(user_query)

        st.session_state.messages.append({"role": "user", "content": user_query})

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                ai_response_message, is_user_text_intent_harmful = ask_ai(user_query)
                if str(is_user_text_intent_harmful).lower()=="true":
                    call_emergency()
                    st.markdown(ai_response_message)
                else:
                    st.markdown(ai_response_message)

        st.session_state.messages.append(
            {"role": "assistant", "content": ai_response_message}
        )

        st.session_state.is_generating = False  # 🟢 unlock UI
        



if __name__ == "__main__":
    main()