import streamlit as st

st.set_page_config(layout="wide")

pages = [
    st.Page("main_chat.py", title="Chat", icon="🤖"),
    st.Page("therapist_finder.py", title="Nearby Therapist", icon="📍"),
    st.Page("meds_scheduler.py", title="Medicine Schedule", icon="💊"),
    st.Page("configure_setting.py", title="Setting", icon=":material/settings:"),
]


pg = st.navigation(pages, position="top")
pg.run()

