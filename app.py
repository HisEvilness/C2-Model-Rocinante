import streamlit as st
import pandas as pd

# Title
st.title("Casualty Dashboard: Russo-Ukrainian Conflict")

# Sidebar Inputs
with st.sidebar:
    st.header("Scenario Settings")

    # Conflict Duration
    duration_days = st.slider("Duration of Conflict (Days)", min_value=30, max_value=1500, step=30, value=1031)

    # Commander Effect
    commander_effect_rus = st.slider("Russian Commander Efficiency", 0.8, 1.2, 1.1, 0.01)
    commander_effect_ukr = st.slider("Ukrainian Commander Efficiency", 0.8, 1.2, 0.9, 0.01)

    # EW Effect
    ew_effect_rus = st.slider("Russian Electronic Warfare Impact", 0.8, 1.2, 0.9, 0.01)
    ew_effect_ukr = st.slider("Ukrainian Electronic Warfare Impact", 0.8, 1.2, 1.1, 0.01)

    # Morale Effect
    morale_rus = st.slider("Russian Morale Factor", 0.8, 1.2, 1.1, 0.01)
    morale_ukr = st.slider("Ukrainian Morale Factor", 0.8, 1.2, 0.9, 0.01)

    # Medical Support
    medical_rus = st.slider("Russian Medical Support Efficiency", 0.8, 1.2, 1.1, 0.01)
    medical_ukr = st.slider("Ukrainian Medical Support Efficiency", 0.8, 1.2, 0.9, 0.01)

# Weapon System Efficiency Baseline
weapon_systems = {
    "Artillery": 0.70,
    "Drones": 0.10,
    "Snipers": 0.02,
    "Small Arms": 0.05,
    "Heavy Weapons": 0.05,
    "Armored Vehicles": 0.05,
    "Air Strikes": 0.03
}

# Unit casualty factors
unit_casualty_factors = {
    "Mechanized": (60, 150),
    "Infantry": (80, 200),
    "VDV (Airborne)": (70, 170),
    "Marines": (75, 190),
    "Armored": (100, 220),
    "Volunteer Units": (130, 300),
    "Territorial Defense Units": (100, 240),
    "PMCs": (90, 210)
}

# Country Units Selection
rus_units = st.multiselect("Russian Units", options=list(unit_casualty_factors.keys()), default=[
    "Mechanized", "Infantry", "VDV (Airborne)", "Marines", "Armored", "Territorial Defense Units", "PMCs"])
ukr_units = st.multiselect("Ukrainian Units", options=list(unit_casualty_factors.keys()), default=list(unit_casualty_factors.keys()))

def calculate_casualties(units, duration, commander_eff, ew_eff, morale, medical):
    low_total, high_total = 0, 0
    ew_effect = 1.0 - (ew_eff - 1.0)
    medical_effect = 1.0 - (medical - 1.0)
    for unit in units:
        low, high = unit_casualty_factors[unit]
        low *= duration
        high *= duration
        adj_low = int(low * commander_eff * morale * ew_effect * medical_effect)
        adj_high = int(high * commander_eff * morale * ew_effect * medical_effect)
        low_total += adj_low
        high_total += adj_high
    return low_total, high_total

def calculate_by_weapon(total_low, total_high):
    data = {}
    for k, v in weapon_systems.items():
        data[k] = {
            "Low Estimate": int(total_low * v),
            "High Estimate": int(total_high * v)
        }
    return pd.DataFrame(data).T

# Compute Casualties
rus_low, rus_high = calculate_casualties(rus_units, duration_days, commander_effect_rus, ew_effect_rus, morale_rus, medical_rus)
ukr_low, ukr_high = calculate_casualties(ukr_units, duration_days, commander_effect_ukr, ew_effect_ukr, morale_ukr, medical_ukr)

# Display Russia
st.header("🇷🇺 Russian Forces")
df_rus = calculate_by_weapon(rus_low, rus_high)
st.subheader("Casualties by Weapon System")
st.dataframe(df_rus)
st.metric("Total Casualties (Low)", f"{rus_low:,}")
st.metric("Total Casualties (High)", f"{rus_high:,}")

# Display Ukraine
st.header("🇺🇦 Ukrainian Forces")
df_ukr = calculate_by_weapon(ukr_low, ukr_high)
st.subheader("Casualties by Weapon System")
st.dataframe(df_ukr)
st.metric("Total Casualties (Low)", f"{ukr_low:,}")
st.metric("Total Casualties (High)", f"{ukr_high:,}")

# Footer
st.caption("Model based on empirical casualty rates, adjusted for commander effect, morale, EW, and medical support. Survival rate logic temporarily disabled to improve model integrity.")
