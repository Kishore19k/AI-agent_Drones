import streamlit as st
import pandas as pd
from datetime import datetime

# ======================================================
# Page config
# ======================================================
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
# Normalize columns (SAFE)
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
# Mission selection
# ======================================================
st.subheader("🎯 Select Mission")
mission_index = st.selectbox("Choose Mission", missions.index)
mission = missions.loc[mission_index]

st.write("### Mission Details")
st.json(mission.to_dict())

# ======================================================
# 💬 Chatbot Section (AFTER mission selection)
# ======================================================
st.subheader("💬 Drone Ops Chat Assistant")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Ask me about assignment, risks, or decisions...")

if user_input:
    st.session_state.chat_history.append(
        {"role": "user", "content": user_input}
    )

    text = user_input.lower()
    response = ""

    if "assign" in text:
        response = "Click **Run Assignment Agent** to generate a pilot and drone assignment for the selected mission."

    elif "why" in text:
        response = (
            "Assignments are based on pilot skills, certifications, availability, "
            "location match, drone availability, weather compatibility, and budget."
        )

    elif "risk" in text or "conflict" in text:
        response = (
            "I check for weather risks, maintenance issues, location mismatches, "
            "certification gaps, and budget overruns."
        )

    elif "weather" in text:
        response = (
            "For rainy missions, IP43 drones are preferred. "
            "If unavailable, I allow assignment with a weather risk alert."
        )

    else:
        response = (
            "You can ask me to assign a mission, explain risks, "
            "or clarify why a pilot or drone was chosen."
        )

    st.session_state.chat_history.append(
        {"role": "assistant", "content": response}
    )

    with st.chat_message("assistant"):
        st.markdown(response)

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
    # Pilot Matching (SOFT)
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
    # Drone Matching (SOFT)
    # --------------------------------------------------
    matching_drones = drones[
        (drones["status"].str.contains("available")) &
        (drones["location"] == mission_location)
    ]

    if matching_drones.empty:
        st.error("❌ No drone available at mission location.")
        st.stop()

    # Weather handling (WARN, DON’T FAIL)
    weather_warning = False

    if mission_weather == "rainy":
        ip43_drones = matching_drones[
            matching_drones["weather_resistance"] == "IP43"
        ]
        if not ip43_drones.empty:
            matching_drones = ip43_drones
        else:
            weather_warning = True

    drone = matching_drones.iloc[0]

    # ==================================================
    # Output Assignment
    # ==================================================
    st.success("✅ Assignment Generated")

    st.subheader("👨‍✈️ Assigned Pilot")
    st.json(pilot.to_dict())

    st.subheader("🚁 Assigned Drone")
    st.json(drone.to_dict())

    # ==================================================
    # Conflict / Risk Detection
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

    if weather_warning:
        conflicts.append("Weather risk: non-IP43 drone assigned in rainy conditions")

    # ==================================================
    # Final Decision Explanation
    # ==================================================
    if conflicts:
        st.warning("⚠ Alerts / Risks Identified:")
        for c in conflicts:
            st.write("-", c)
    else:
        st.info("No conflicts detected. Mission ready to proceed.")
