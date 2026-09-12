import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Skylight Live AIS Portal", page_icon="📡", layout="wide")
st.title("📡 Live AIS Tracking & Satellite Detection Center")
st.caption("Direct API Key Streaming Integration")
st.markdown("---")

# --- SIDEBAR INTERFACE ---
st.sidebar.subheader("🔑 Secure Authentication")
st.sidebar.write("Generate an API Key from your Skylight account dashboard settings.")
API_KEY = st.sidebar.text_input("Enter Skylight API Key", type="password", value="YOUR_SKYLIGHT_API_KEY")

# 1. LIVE DATA EXTRACTOR USING AN AUTOCONFIGURED HEADER
def fetch_skylight_data(api_key):
    endpoint = "https://api.skylight.earth/graphql"
    
    # Standard headers for an API-token based handshake
    headers = {
        "Authorization": f"ApiKey {api_key}",  # Can also try f"Bearer {api_key}" if provisioned as a token
        "Content-Type": "application/json"
    }
    
    # Minimalist query to pull localized coordinate updates
    query = """
    query {
      searchEventsV2(input: { limit: 50 }) {
        records {
          eventId
          eventType
          latitude
          longitude
        }
      }
    }
    """
    
    try:
        if api_key == "YOUR_SKYLIGHT_API_KEY":
            return None, "Simulation Mode active. Enter a valid key to link live streams."
            
        res = requests.post(endpoint, json={'query': query}, headers=headers, timeout=10)
        
        if res.status_code == 200:
            data = res.json()
            if 'data' in data and data['data'] and 'searchEventsV2' in data['data']:
                return data['data']['searchEventsV2']['records'], "SECURE"
            else:
                return None, f"Connected, but response was empty or structural format modified."
        elif res.status_code == 401:
            return None, "401 Unauthorized: Try switching prefix format to 'Bearer' or verify key rights."
        else:
            return None, f"HTTP Error {res.status_code} received from server."
            
    except Exception as e:
        return None, f"Network Error: {str(e)}"

# Execute feed lookup
events_data, system_status = fetch_skylight_data(API_KEY)

# Sidebar connection feedback
with st.sidebar.expander("🛠️ Connection Diagnostics"):
    if system_status == "SECURE":
        st.success("Data Stream: ACTIVE")
    else:
        st.warning(f"Status: {system_status}")

# 2. LOCAL FALLBACK IN CASE KEY IS REJECTED
if not events_data:
    events_data = [
        {"eventId": "SIM-001", "eventType": "AIS Correlated Target", "latitude": -4.0435, "longitude": 39.6682},
        {"eventId": "SIM-002", "eventType": "Dark Hull Detection (SAR)", "latitude": -5.5000, "longitude": 43.1200},
        {"eventId": "SIM-003", "eventType": "Rendezvous / Transshipment", "latitude": -4.6222, "longitude": 55.4514},
        {"eventId": "SIM-004", "eventType": "EEZ Incursion Alert", "latitude": -12.2725, "longitude": 49.2892}
    ]

# 3. GRAPHICAL VISUALIZATION LAYER
processed_list = [{
    "Event ID": ev.get("eventId"),
    "Classification": ev.get("eventType"),
    "Latitude": ev.get("latitude"),
    "Longitude": ev.get("longitude")
} for ev in events_data]

df_events = pd.DataFrame(processed_list)

col_map, col_table = st.columns([3, 2])

with col_map:
    st.subheader("🌐 Real-Time Operational Map")
    st.map(df_events, latitude="Latitude", longitude="Longitude", size=50, zoom=4)
    
with col_table:
    st.subheader("🚨 Tracked Targets")
    st.dataframe(df_events, use_container_width=True, hide_index=True)
    st.markdown("---")
    st.metric("Total Monitored Contacts", len(df_events))