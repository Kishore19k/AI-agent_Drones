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

    # Debug view (optional but helpful)
    # st.write("Pilot Columns:", pilots.columns.tolist())
    # st.write("Drone Columns:", drones.columns.tolist())
    # st.write("Mission Columns:", missions.columns.tolist())

    # ---------- SELECT MISSION ----------
    st.subheader("🎯 Select Mission")
    mission_index = st.selectbox("Choose Mission", missions.index)
    mission = missions.loc[mission_index]

    st.write("### Mission Details")
    st.json(mission.to_dict())

    # ---------- ASSIGNMENT LOGIC ----------
    if st.button("Run Assignment Agent"):

        # -------- SAFE COLUMN DETECTION --------

        # Detect skill column dynamically
        skill_column = None
        for col in pilots.columns:
            if "skill" in col.lower():
                skill_column = col
                break

        if skill_column is None:
            st.error("❌ No skill-related column found in Pilot CSV")
            st.stop()

        # Normalize skill text
        pilots[skill_column] = pilots[skill_column].fillna("").astype(str).str.lower()
        mission_skill = str(mission.get("required_skills", "")).lower()

        # Normalize status/location columns safely
        if "status" not in pilots.columns or "location" not in pilots.columns:
            st.error("❌ Pilot CSV must contain 'status' and 'location' columns")
            st.stop()

        if "status" not in drones.columns or "location" not in drones.columns:
            st.error("❌ Drone CSV must contain 'status' and 'location' columns")
            st.stop()

        # ---------- FIND MATCHING PILOTS ----------
        matching_pilots = pilots[
            (pilots["status"].astype(str).str.lower() == "available") &
            (pilots[skill_column].str.contains(mission_skill)) &
            (pilots["location"] == mission.get("location"))
        ]

        # ---------- FIND MATCHING DRONES ----------
        matching_drones = drones[
            (drones["status"].astype(str).str.lower() == "available") &
            (drones["location"] == mission.get("location"))
        ]

        # Weather rule (if column exists)
        if "weather" in mission and "weather_rating" in drones.columns:
            if str(mission["weather"]).lower() == "rainy":
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

            # Skill check
            if mission_skill not in pilot[skill_column]:
                conflicts.append("Skill mismatch")

            # Maintenance check
            if "maintenance" in drone["status"].lower():
                conflicts.append("Drone under maintenance")

            # Weather compatibility
            if "weather" in mission and "weather_rating" in drones.columns:
                if str(mission["weather"]).lower() == "rainy" and drone.get("weather_rating") != "IP43":
                    conflicts.append("Weather compatibility issue")

            # Location mismatch
            if pilot["location"] != drone["location"]:
                conflicts.append("Location mismatch")

            # Budget check (safe)
            daily_rate = pilot.get("daily_rate", 0)
            duration = mission.get("duration_days", 0)
            budget = mission.get("budget", 0)

            try:
                cost = float(daily_rate) * float(duration)
                if budget and cost > float(budget):
                    conflicts.append("Budget overrun")
            except:
                pass

            # Display conflicts
            if conflicts:
                st.warning("⚠ Conflicts Detected:")
                for c in conflicts:
                    st.write("-", c)
            else:
                st.info("No conflicts detected. Mission ready.")

else:
    st.warning("Please upload all three CSV files to continue.")
