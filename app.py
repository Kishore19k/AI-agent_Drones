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
# Normalize Text Columns (SAFE)
# ======================================================
pilots["skills"] = pilots["skills"].fillna("").astype(str).str.lower()
pilots["certifications"] = pilots["certifications"].fillna("").astype(str).str.lower()
pilots["status"] = pilots["status"].fillna("").astype(str).str.lower()

drones["status"] = drones["status"].fillna("").astype(str).str.lower()
drones["weather_resistance"] = drones["weather_resistance"].fillna("").astype(str).str.upper()

missions["required_skills"] = missions["required_skills"].fillna("").astype(str).str.lower()
missions["required_certs"] = missions["required_certs"].fillna("").astype(str).str.lower()
missions["weather_forecast"] = missions["weather_forecast"].fillna("").astype(str).str.lower()

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
    # Find Available Pilots (SOFT MATCH)
    # --------------------------------------------------
    matching_pilots = pilots[
        (pilots["status"].str.contains("available")) &
        (pilots["skills"].str.contains(mission_skill)) &
        (pilots["location"] == mission_location)
    ]

    if matching_pilots.empty:
        st.error("❌ No suitable pilot available.")
        st.stop()

    pilot = matching_pilots.iloc[0]

    # --------------------------------------------------
    # Find Available Drones (SOFT MATCH)
    # --------------------------------------------------
    matching_drones = drones[
        (drones["status"].str.contains("available")) &
        (drones["location"] == mission_location)
    ]

    if matching_drones.empty:
        st.error("❌ No drone available at mission location.")
        st.stop()

    # --------------------------------------------------
    # Weather Handling (WARN, DON’T FAIL)
    # --------------------------------------------------
    weather_warning = False

    if mission_weather == "rainy":
        ip43_drones = matching_drones[
            matching_drones["weather_resistance"] == "IP43"
        ]
        if not ip43_drones.empty:
            matching_drones = ip43_drones
        else:
            weather_warning = True  # allow with warning

    drone = matching_drones.iloc[0]

    # ==================================================
    # Assignment Output
    # ==================================================
    st.success("✅ Assignment Generated")

    st.subheader("👨‍✈️ Assigned Pilot")
    st.json(pilot.to_dict())

    st.subheader("🚁 Assigned Drone")
    st.json(drone.to_dict())

    # ==================================================
    # Conflict & Risk Detection
    # ==================================================
    conflicts = []

    if mission_skill not in pilot["skills"]:
        conflicts.append("Skill mismatch")

    if mission_cert not in pilot["certifications"]:
        conflicts.append("Certification mismatch")

    if "maintenance" in drone["status"]:
        conflicts.append("Drone under maintenance")

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

    # Weather warning
    if weather_warning:
        conflicts.append("Weather risk: non-IP43 drone assigned in rainy conditions")

    # ==================================================
    # Display Final Decision
    # ==================================================
    if conflicts:
        st.warning("⚠ Alerts / Risks Identified:")
        for c in conflicts:
            st.write("-", c)
    else:
        st.info("No conflicts detected. Mission ready to proceed.")
