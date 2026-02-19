import streamlit as st
import pandas as pd

st.set_page_config(page_title="Drone Ops Coordinator AI", layout="wide")
st.title("🚁 Drone Operations Coordinator AI")

# ---------------------------
# Helper: Detect Column by Keywords
# ---------------------------
def detect_column(df, keywords, required=True):
    for col in df.columns:
        for key in keywords:
            if key.lower() in col.lower():
                return col
    if required:
        st.error(f"❌ Could not detect column for {keywords}")
        st.stop()
    return None


# ---------------------------
# Upload CSV Files
# ---------------------------
pilot_file = st.file_uploader("Upload Pilot Roster CSV", type=["csv"])
drone_file = st.file_uploader("Upload Drone Fleet CSV", type=["csv"])
mission_file = st.file_uploader("Upload Missions CSV", type=["csv"])

if pilot_file and drone_file and mission_file:

    pilots = pd.read_csv(pilot_file)
    drones = pd.read_csv(drone_file)
    missions = pd.read_csv(mission_file)

    st.success("All files loaded successfully ✅")

    # ---------------------------
    # Auto Detect Important Columns
    # ---------------------------
    pilot_skill_col = detect_column(pilots, ["skill"])
    pilot_status_col = detect_column(pilots, ["status"])
    pilot_location_col = detect_column(pilots, ["location"])
    pilot_name_col = detect_column(pilots, ["name"], required=False)
    pilot_rate_col = detect_column(pilots, ["rate", "cost", "salary"], required=False)

    drone_status_col = detect_column(drones, ["status"])
    drone_location_col = detect_column(drones, ["location"])
    drone_id_col = detect_column(drones, ["id"])
    drone_weather_col = detect_column(drones, ["weather", "rating"], required=False)

    mission_skill_col = detect_column(missions, ["skill"])
    mission_location_col = detect_column(missions, ["location"])
    mission_weather_col = detect_column(missions, ["weather"], required=False)
    mission_budget_col = detect_column(missions, ["budget"], required=False)
    mission_duration_col = detect_column(missions, ["duration", "days"], required=False)

    # Normalize text columns
    pilots[pilot_skill_col] = pilots[pilot_skill_col].fillna("").astype(str).str.lower()
    pilots[pilot_status_col] = pilots[pilot_status_col].astype(str).str.lower()
    drones[drone_status_col] = drones[drone_status_col].astype(str).str.lower()

    # ---------------------------
    # Select Mission
    # ---------------------------
    st.subheader("🎯 Select Mission")
    mission_index = st.selectbox("Choose Mission", missions.index)
    mission = missions.loc[mission_index]

    st.write("### Mission Details")
    st.json(mission.to_dict())

    # ---------------------------
    # Assignment Logic
    # ---------------------------
    if st.button("Run Assignment Agent"):

        mission_skill = str(mission[mission_skill_col]).lower()
        mission_location = mission[mission_location_col]

        # ---- Find Available Pilots ----
        matching_pilots = pilots[
            (pilots[pilot_status_col] == "available") &
            (pilots[pilot_skill_col].str.contains(mission_skill)) &
            (pilots[pilot_location_col] == mission_location)
        ]

        # ---- Find Available Drones ----
        matching_drones = drones[
            (drones[drone_status_col] == "available") &
            (drones[drone_location_col] == mission_location)
        ]

        # ---- Weather Rule ----
        if mission_weather_col and drone_weather_col:
            mission_weather = str(mission[mission_weather_col]).lower()
            if mission_weather == "rainy":
                matching_drones = matching_drones[
                    drones[drone_weather_col].str.upper() == "IP43"
                ]

        # ---------------------------
        # Display Results
        # ---------------------------
        if matching_pilots.empty:
            st.error("❌ No suitable pilot available.")
            st.stop()

        if matching_drones.empty:
            st.error("❌ No suitable drone available.")
            st.stop()

        pilot = matching_pilots.iloc[0]
        drone = matching_drones.iloc[0]

        st.success("✅ Assignment Successful")

        st.subheader("👨‍✈️ Assigned Pilot")
        st.json(pilot.to_dict())

        st.subheader("🚁 Assigned Drone")
        st.json(drone.to_dict())

        # ---------------------------
        # Conflict Detection
        # ---------------------------
        conflicts = []

        if mission_skill not in pilot[pilot_skill_col]:
            conflicts.append("Skill mismatch")

        if "maintenance" in drone[drone_status_col]:
            conflicts.append("Drone under maintenance")

        if mission_weather_col and drone_weather_col:
            if mission_weather == "rainy" and drone[drone_weather_col] != "IP43":
                conflicts.append("Weather compatibility issue")

        if pilot[pilot_location_col] != drone[drone_location_col]:
            conflicts.append("Location mismatch")

        # Budget Check
        if pilot_rate_col and mission_budget_col and mission_duration_col:
            try:
                cost = float(pilot[pilot_rate_col]) * float(mission[mission_duration_col])
                if cost > float(mission[mission_budget_col]):
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
    st.warning("Please upload all three CSV files.")
