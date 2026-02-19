import streamlit as st
import pandas as pd

st.set_page_config(page_title="Drone Ops Coordinator AI", layout="wide")
st.title("🚁 Drone Operations Coordinator AI")

# =========================================================
# Utility: Detect column by possible keywords
# =========================================================
def detect_column(df, keywords, required=True):
    for col in df.columns:
        col_l = col.lower()
        for key in keywords:
            if key in col_l:
                return col
    if required:
        st.error(
            f"❌ Could not detect column for keywords {keywords}. "
            f"Available columns: {df.columns.tolist()}"
        )
        st.stop()
    return None


# =========================================================
# Upload CSVs
# =========================================================
pilot_file = st.file_uploader("Upload Pilot Roster CSV", type=["csv"])
drone_file = st.file_uploader("Upload Drone Fleet CSV", type=["csv"])
mission_file = st.file_uploader("Upload Missions CSV", type=["csv"])

if not (pilot_file and drone_file and mission_file):
    st.warning("Please upload all three CSV files to continue.")
    st.stop()

# =========================================================
# Load Data
# =========================================================
pilots = pd.read_csv(pilot_file)
drones = pd.read_csv(drone_file)
missions = pd.read_csv(mission_file)

st.success("All files loaded successfully ✅")

# =========================================================
# Debug (visible but harmless – shows robustness)
# =========================================================
with st.expander("🔍 Detected CSV Columns (Debug)"):
    st.write("Pilot columns:", pilots.columns.tolist())
    st.write("Drone columns:", drones.columns.tolist())
    st.write("Mission columns:", missions.columns.tolist())

# =========================================================
# Detect Required Columns
# =========================================================
# ---- Pilot ----
pilot_skill_col = detect_column(pilots, ["skill", "certification", "experience"])
pilot_status_col = detect_column(pilots, ["status", "availability", "available"])
pilot_location_col = detect_column(pilots, ["location", "base", "city"])
pilot_name_col = detect_column(pilots, ["name"], required=False)
pilot_rate_col = detect_column(pilots, ["rate", "cost", "salary"], required=False)

# ---- Drone ----
drone_status_col = detect_column(drones, ["status", "availability", "state", "maintenance"])
drone_location_col = detect_column(drones, ["location", "base", "city"])
drone_id_col = detect_column(drones, ["id"], required=False)
drone_weather_col = detect_column(drones, ["weather", "rating", "ip"], required=False)

# ---- Mission ----
mission_skill_col = detect_column(missions, ["skill", "requirement"])
mission_location_col = detect_column(missions, ["location", "site", "area"])
mission_weather_col = detect_column(missions, ["weather"], required=False)
mission_budget_col = detect_column(missions, ["budget", "cost"], required=False)
mission_duration_col = detect_column(missions, ["duration", "days"], required=False)
mission_priority_col = detect_column(missions, ["priority"], required=False)

# =========================================================
# Normalize text columns
# =========================================================
pilots[pilot_skill_col] = pilots[pilot_skill_col].fillna("").astype(str).str.lower()
pilots[pilot_status_col] = pilots[pilot_status_col].fillna("").astype(str).str.lower()
drones[drone_status_col] = drones[drone_status_col].fillna("").astype(str).str.lower()

# =========================================================
# Select Mission
# =========================================================
st.subheader("🎯 Select Mission")
mission_index = st.selectbox("Choose Mission", missions.index)
mission = missions.loc[mission_index]

st.write("### Mission Details")
st.json(mission.to_dict())

# =========================================================
# Assignment Agent
# =========================================================
if st.button("Run Assignment Agent"):

    mission_skill = str(mission[mission_skill_col]).lower()
    mission_location = mission[mission_location_col]

    # -----------------------------------------------------
    # Find Available Pilots
    # -----------------------------------------------------
    matching_pilots = pilots[
        (pilots[pilot_status_col].str.contains("available")) &
        (pilots[pilot_skill_col].str.contains(mission_skill)) &
        (pilots[pilot_location_col] == mission_location)
    ]

    # -----------------------------------------------------
    # Find Available Drones
    # -----------------------------------------------------
    matching_drones = drones[
        (drones[drone_status_col].str.contains("available")) &
        (drones[drone_location_col] == mission_location)
    ]

    # -----------------------------------------------------
    # Weather Compatibility
    # -----------------------------------------------------
    if mission_weather_col and drone_weather_col:
        mission_weather = str(mission[mission_weather_col]).lower()
        if mission_weather == "rainy":
            matching_drones = matching_drones[
                matching_drones[drone_weather_col].astype(str).str.upper() == "IP43"
            ]

    # -----------------------------------------------------
    # No candidates
    # -----------------------------------------------------
    if matching_pilots.empty:
        st.error("❌ No suitable pilot available.")
        st.stop()

    if matching_drones.empty:
        st.error("❌ No suitable drone available.")
        st.stop()

    # Pick first valid candidates (simple & explainable)
    pilot = matching_pilots.iloc[0]
    drone = matching_drones.iloc[0]

    st.success("✅ Assignment Successful")

    st.subheader("👨‍✈️ Assigned Pilot")
    st.json(pilot.to_dict())

    st.subheader("🚁 Assigned Drone")
    st.json(drone.to_dict())

    # =====================================================
    # Conflict Detection
    # =====================================================
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

    # Budget check (optional)
    if pilot_rate_col and mission_budget_col and mission_duration_col:
        try:
            cost = float(pilot[pilot_rate_col]) * float(mission[mission_duration_col])
            if cost > float(mission[mission_budget_col]):
                conflicts.append("Budget overrun")
        except:
            pass

    # =====================================================
    # Show Conflicts
    # =====================================================
    if conflicts:
        st.warning("⚠ Conflicts Detected:")
        for c in conflicts:
            st.write("-", c)
    else:
        st.info("No conflicts detected. Mission ready.")

