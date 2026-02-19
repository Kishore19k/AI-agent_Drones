import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Drone Ops Coordinator AI", layout="wide")
st.title("🚁 Drone Operations Coordinator AI")

# ======================================================
# Upload CSVs
# ======================================================
pilot_file = st.file_uploader("Upload Pilot Roster CSV", type=["csv"])
drone_file = st.file_uploader("Upload Drone Fleet CSV", type=["csv"])
mission_file = st.file_uploader("Upload Missions CSV", type=["csv"])

if not (pilot_file and drone_file and mission_file):
    st.warning("Please upload all three CSV files.")
    st.stop()

# ======================================================
# Load Data
# ======================================================
pilots = pd.read_csv(pilot_file)
drones = pd.read_csv(drone_file)
missions = pd.read_csv(mission_file)

st.success("All files loaded successfully ✅")

# ======================================================
# Normalize Text Columns (Safe)
# ======================================================
pilots["skills"] = pilots["skills"].fillna("").str.lower()
pilots["certifications"] = pilots["certifications"].fillna("").str.lower()
pilots["status"] = pilots["status"].fillna("").str.lower()

drones["status"] = drones["status"].fillna("").str.lower()
drones["weather_resistance"] = drones["weather_resistance"].fillna("").str.upper()

missions["required_skills"] = missions["required_skills"].fillna("").str.lower()
missions["required_certs"] = missions["required_certs"].fillna("").str.lower()
missions["weather_forecast"] = missions["weather_forecast"].fillna("").str.lower()

# ======================================================
# Select Mission
# ======================================================
st.subheader("🎯 Select Mission")
mission_index = st.selectbox("Choose Mission", missions.index)
mission = missions.loc[mission_index]

st.write("### Mission Details")
st.json(mission.to_dict())

# ======================================================
# Assignment Agent
# ======================================================
if st.button("Run Assignment Agent"):

    mission_location = mission["location"]
    mission_skill = mission["required_skills"]
    mission_cert = mission["required_certs"]
    mission_weather = mission["weather_forecast"]
    mission_budget = mission["mission_budget_inr"]

    # --------------------------------------------------
    # Find Available Pilots
    # --------------------------------------------------
    matching_pilots = pilots[
        (pilots["status"] == "available") &
        (pilots["skills"].str.contains(mission_skill)) &
        (pilots["certifications"].str.contains(mission_cert)) &
        (pilots["location"] == mission_location)
    ]

    # --------------------------------------------------
    # Find Available Drones
    # --------------------------------------------------
    matching_drones = drones[
        (drones["status"] == "available") &
        (drones["location"] == mission_location)
    ]

    # Weather compatibility
    if mission_weather == "rainy":
        matching_drones = matching_drones[
            matching_drones["weather_resistance"] == "IP43"
        ]

    # --------------------------------------------------
    # No Matches
    # --------------------------------------------------
    if matching_pilots.empty:
        st.error("❌ No suitable pilot available.")
        st.stop()

    if matching_drones.empty:
        st.error("❌ No suitable drone available.")
        st.stop()

    # Select first valid candidates
    pilot = matching_pilots.iloc[0]
    drone = matching_drones.iloc[0]

    st.success("✅ Assignment Successful")

    st.subheader("👨‍✈️ Assigned Pilot")
    st.json(pilot.to_dict())

    st.subheader("🚁 Assigned Drone")
    st.json(drone.to_dict())

    # ==================================================
    # Conflict Detection
    # ==================================================
    conflicts = []

    if mission_skill not in pilot["skills"]:
        conflicts.append("Skill mismatch")

    if mission_cert not in pilot["certifications"]:
        conflicts.append("Certification mismatch")

    if "maintenance" in drone["status"]:
        conflicts.append("Drone under maintenance")

    if mission_weather == "rainy" and drone["weather_resistance"] != "IP43":
        conflicts.append("Weather compatibility issue")

    if pilot["location"] != drone["location"]:
        conflicts.append("Location mismatch")

    # Budget check
    try:
        start = pd.to_datetime(mission["start_date"])
        end = pd.to_datetime(mission["end_date"])
        days = (end - start).days + 1
        cost = pilot["daily_rate_inr"] * days

        if cost > mission_budget:
            conflicts.append("Budget overrun")
    except:
        pass

    # ==================================================
    # Display Conflicts
    # ==================================================
    if conflicts:
        st.warning("⚠ Conflicts Detected:")
        for c in conflicts:
            st.write("-", c)
    else:
        st.info("No conflicts detected. Mission ready.")

