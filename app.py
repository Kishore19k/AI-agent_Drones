import streamlit as st
import pandas as pd

st.set_page_config(page_title="Drone Ops Coordinator AI", layout="centered")

st.title("🚁 Drone Operations Coordinator AI")
st.write("Upload pilot, drone, and mission data to let the agent assist you.")

# Upload CSV files
pilot_file = st.file_uploader("Upload Pilot Roster CSV", type=["csv"])
drone_file = st.file_uploader("Upload Drone Fleet CSV", type=["csv"])
mission_file = st.file_uploader("Upload Missions CSV", type=["csv"])

if pilot_file and drone_file and mission_file:
    pilots = pd.read_csv(pilot_file)
    drones = pd.read_csv(drone_file)
    missions = pd.read_csv(mission_file)

    st.success("All files loaded successfully ✅")

    st.subheader("📋 Missions Data")
    st.dataframe(missions)

    st.subheader("👨‍✈️ Pilots Data")
    st.dataframe(pilots)

    st.subheader("🚁 Drones Data")
    st.dataframe(drones)

    st.info(
        "Next step: Add agent logic to match pilots and drones to missions "
        "and detect conflicts."
    )
else:
    st.warning("Please upload all three CSV files to continue.")

