import streamlit as st
import pandas as pd

st.title("🚁 Drone Coordinator AI")

pilot_file = st.file_uploader("Upload Pilot CSV", type="csv")
drone_file = st.file_uploader("Upload Drone CSV", type="csv")
mission_file = st.file_uploader("Upload Mission CSV", type="csv")

if pilot_file and drone_file and mission_file:
    pilots = pd.read_csv(pilot_file)
    drones = pd.read_csv(drone_file)
    missions = pd.read_csv(mission_file)

    st.success("Files loaded successfully!")
    st.dataframe(missions)
