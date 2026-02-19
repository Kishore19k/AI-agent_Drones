import streamlit as st
import pandas as pd

st.set_page_config(page_title="Drone Ops Coordinator AI", layout="wide")

st.title("🚁 Drone Operations Coordinator AI")

pilot_file = st.file_uploader("Upload Pilot Roster CSV", type=["csv"])
drone_file = st.file_uploader("Upload Drone Fleet CSV", type=["csv"])
mission_file = st.file_uploader("Upload Missions CSV", type=["csv"])

if pilot_file and drone_file and mission_file:

    pilots = pd.read_csv(pilot_file)
    drones = pd.read_csv(drone_file)
    missions = pd.read_csv(mission_file)

    st.success("All files loaded successfully ✅")

    # ---------- SELECT MISSION ----------
    st.subheader("🎯 Select Mission")
    mission_index = st.selectbox("Choose Mission", missions.index)
    mission = missions.loc[mission_index]

    st.write("### Mission Details")
    st.json(mission.to_dict())

    # ---------- ASSIGNMENT LOGIC ----------
    if st.button("Run Assignment Agent"):

        # Normalize text
        pilots["skills"] = pilots["skills"].fillna("").str.lower()
        mission_skill = str(mission["required_skills"]).lower()

        # ---------- FIND MATCHING PILOTS ----------
        matching_pilots = pilots[
            (pilots["status"] == "Available") &
            (pilots["skills"].str.contains(mission_skill)) &
            (pilots["location"] == mission["location"])
        ]

        # ---------- FIND MATCHING DRONES ----------
        matching_drones = drones[
            (drones["status"] == "Available") &
            (drones["location"] == mission["location"])
        ]

        # Weather rule
        if mission["weather"] == "Rainy":
            matching_drones = matching_drones[
                matching_drones["weather_rating"] == "IP43"
            ]

        # ---------- RESULTS ----------
        if matching_pilots.empty:
            st.error("❌ No suitable pilot available.")
        elif matching_drones.empty:
            st.error("❌ No suitable drone available.")
        else:
            pilot = matching_pilots.iloc[0]
            drone = matching_drones.iloc[0]

            st.success("✅ Assignment Successful")

            st.subheader("👨‍✈️ Assigned Pilot")
            st.json(pilot.to_dict())

            st.subheader("🚁 Assigned Drone")
            st.json(drone.to_dict())

            # ---------- CONFLICT CHECK ----------
            conflicts = []

            if mission_skill not in pilot["skills"]:
                conflicts.append("Skill mismatch")

            if drone["status"] == "Maintenance":
                conflicts.append("Drone under maintenance")

            if mission["weather"] == "Rainy" and drone["weather_rating"] != "IP43":
                conflicts.append("Weather compatibility issue")

            if pilot["location"] != drone["location"]:
                conflicts.append("Location mismatch")

            cost = pilot["daily_rate"] * mission["duration_days"]

            if cost > mission["budget"]:
                conflicts.append("Budget overrun")

            if conflicts:
                st.warning("⚠ Conflicts Detected:")
                for c in conflicts:
                    st.write("-", c)
            else:
                st.info("No conflicts detected. Mission ready.")

else:
    st.warning("Please upload all three CSV files to continue.")
