import os
import json
import requests
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from google import genai
from google.genai import types
from dotenv import load_dotenv


load_dotenv()


DB_FILE = r"Database\user_data.db"

st.markdown("""
<style>
.st-emotion-cache-zh2fnc {
    width: fit-content;
    height: auto;
    max-width: 100%;
    min-width: 1rem;
    position: relative;
    overflow: visible;
    top: 28px;
    left: 36px;
}           
            
</style<>

""",unsafe_allow_html=True)


def get_coordinates(address):
    url = "https://nominatim.openstreetmap.org/search"
    headers = {'User-Agent': 'TherapistFinderApp/1.0'}
    params = {
        'q': address,
        'format': 'json',
        'limit': 1
    }
    
    try:
        response = requests.get(url, params=params, headers=headers).json()
        if response:
            return float(response[0]['lat']), float(response[0]['lon'])
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None, None

def find_nearby_therapists(address,lat, lon, radius_meters=5000):
    try:

        client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"),
        )

        model = "gemini-flash-latest"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=f"""
    Input:
    - City: {address}
    - Latitude: {lat}
    - Longitude: {lon}
    - Radius: {radius_meters} meters

    """),
                ],
            ),
        ]
        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_budget=-1,
            ),
            system_instruction=[
                types.Part.from_text(text="""You are a healthcare location extraction assistant.

    Your task:
    Find ONLY mental health related healthcare providers within a 5-10 km radius
    around the given latitude and longitude.


    Include ONLY places related to mental health, such as:
    - Psychiatrist
    - Psychologist
    - Psychotherapist
    - Mental health clinic
    - Psychiatry hospital / department

    STRICTLY EXCLUDE:
    - Eye clinics
    - Skin / dermatology clinics
    - Dental clinics
    - ENT clinics
    - General physician clinics (unless explicitly mental health related)

    Return ONLY valid JSON in the following format:
    [
    {
        \"type\": \"node\",
        \"id\": number,
        \"lat\": number,
        \"lon\": number,
        \"tags\": {
        \"amenity\": \"clinic | doctors | hospital\",
        \"healthcare\": \"psychiatrist | psychologist | psychotherapist | mental_health\",
        \"name\": \"string\",
        \"addr:full\": \"string (find address if not available then find landmark or nearby town/city location)\",
        \"addr:district\": \"string (if available)\",
        \"addr:state\": \"string (if available)\"
        }
    }
    ]

    Rules:
    - !IMP Find exact Latitude and Longitude of the clinic/hospitals very precisely
    - Do NOT include explanations
    - Do NOT include markdown
    - Do NOT hallucinate non-mental-health facilities
    - If no results are found, return an empty array []
    """),
            ],
        )
        output_chunk = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text:
                output_chunk += chunk.text

        return output_chunk
    except Exception as e:
        st.markdown("Set your Google Gemini API key in Settings")
        print(e)





# ---------- TITLE ----------
st.set_page_config(page_title="Find Therapists Near You", layout="wide")

st.markdown(
    "<h1 style='text-align: center;'>Find Therapists Near You</h1>",
    unsafe_allow_html=True
)

st.write("")

    # ---------- LOCATION SEARCH ----------


with st.form("search_form"):
    col1, col2 = st.columns([4, 1])

    with col1:
        user_residency_location = st.text_input("Search location", placeholder="Eg: Nerul, Navi Mumbai")

    with col2:
        submitted = st.form_submit_button("Search 🔍")


latitude_user, longitude_user = get_coordinates(user_residency_location)
raw_data_str = find_nearby_therapists(address=user_residency_location,lat=latitude_user,lon=longitude_user)
raw_data = json.loads(raw_data_str)
print(raw_data)
results = []
locations = []

for place in raw_data:
    tags = place.get("tags", {})

    name = tags.get("name", "Unknown Clinic")

    address = (
        tags.get("addr:full")
        or tags.get("addr:district")
        or "Address Not Available"
    )


    lat = place.get("lat")
    lng = place.get("lon")

    results.append({
        "name": name,
        "address": address,
        "lat": lat,
        "lng": lng
    })

    locations.append({
        "lat":lat,
        "lng":lng,
        "label":name,
    })



st.write("")


if results:
    table_data = []

    for r in results:
        map_link = f"https://www.google.com/maps?q={r['lat']},{r['lng']}"
        # map_link = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={}&key={os.getenv('GEMINI_API_KEY')}"

        table_data.append({
                "Clinic Name": r.get("name", "Unnamed"),
                "Address": r.get("address", "Address not available"),
                "Google Map Link": map_link
            })

    df = pd.DataFrame(table_data)


    st.subheader("Available Therapists")
    st.dataframe(
    df,
    column_config={
        "Google Map Link": st.column_config.LinkColumn(
            "Google Map Link",
            display_text="View on Map 📍"
        )
    },
    width='stretch'
    )

        # ---------- LIVE MAP ----------
    st.subheader("Map View")

    
    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        #map {{
        height: 100%;
        width: 100%;
        }}
        html, body {{
        height: 100%;
        margin: 0;
        padding: 0;
        }}
    </style>
    </head>
    <body>
    <div id="map"></div>

    <script>
    function initMap() {{
    const center = {{ lat: {locations[0]['lat']}, lng: {locations[0]['lng']} }};
    const map = new google.maps.Map(document.getElementById("map"), {{
        zoom: 14,
        center: center
    }});

    const locations = {locations};

    locations.forEach(loc => {{
        new google.maps.Marker({{
        position: {{ lat: loc.lat, lng: loc.lng }},
        map: map,
        title: loc.label,
        icon: "http://maps.google.com/mapfiles/ms/icons/red-dot.png"
        }});
        
    }});
    
    }}
    </script>

    <script async
    src="https://maps.googleapis.com/maps/api/js?key={os.getenv("GEMINI_API_KEY")}&callback=initMap">
    </script>

    </body>
    </html>
    """

    components.html(map_html, height=500)

    

else:
    st.info("Search for a location to see therapists nearby.")
