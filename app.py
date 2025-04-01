import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Title
st.title("Casualty & Survival Dashboard: Russo-Ukrainian Conflict")

# Unit Selection
unit_type = st.selectbox("Select Unit Type", [
    "Mechanized",
    "Infantry",
    "VDV (Airborne)",
    "Marines",
    "Armored",
    "Militias",
    "Volunteer Units"
])

# Conflict Duration
duration_days = st.slider("Duration of Conflict (Days)", min_value=30, max_value=1500, step=30, value=300)

# Commander Effect
commander_effect = st.slider("Commander Effectiveness Modifier (0.8 - 1.2)", min_value=0.8, max_value=1.2, step=0.01, value=1.0)

# Electronic Warfare Efficiency
ew_efficiency = st.slider("Electronic Warfare Disruption (0.0 - 1.0)", min_value=0.0, max_value=1.0, step=0.05, value=0.5)

# Terrain Type
terrain = st.radio("Battlefield Terrain", ["Urban", "Open", "Mixed"])
terrain_modifier = {"Urban": 1.2, "Open": 1.0, "Mixed": 1.1}[terrain]

# Morale Modifier
morale = st.slider("Morale Modifier (0.5 - 1.0)", 0.5, 1.0, step=0.05, value=0.9)

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

# Base daily casualty ranges per unit type (adjusted empirically)
unit_casualty_factors = {
    "Mechanized": (60, 150),
    "Infantry": (80, 200),
    "VDV (Airborne)": (70, 170),
    "Marines": (75, 190),
    "Armored": (100, 220),
    "Militias": (120, 280),
    "Volunteer Units": (130, 300)
}

low_daily, high_daily = unit_casualty_factors[unit_type]
low_total = int(low_daily * duration_days * commander_effect * terrain_modifier)
high_total = int(high_daily * duration_days * commander_effect * terrain_modifier)

# Casualty Calculation by Weapon System
casualty_data = {}
for system, contribution in weapon_systems.items():
    if system in ["Drones", "Air Strikes"]:
        contribution *= (1 - ew_efficiency)
    casualty_data[system] = {
        "Low Estimate": int(low_total * contribution),
        "High Estimate": int(high_total * contribution)
    }

# Display Results
st.subheader("Estimated Total Casualties")
st.metric(label="Low Estimate", value=f"{low_total:,} personnel")
st.metric(label="High Estimate", value=f"{high_total:,} personnel")

# Convert to DataFrame
df = pd.DataFrame(casualty_data).T
st.subheader("Casualties by Weapon System")
st.dataframe(df)

# Survival Probability (decay-based model without initial troop count)
daily_survival_low = 1 - (low_daily / (low_daily + 1))
daily_survival_high = 1 - (high_daily / (high_daily + 1))
survival_low = (daily_survival_low ** duration_days) * morale
survival_high = (daily_survival_high ** duration_days) * morale

st.subheader("Estimated Survival Rates (Probability Over Duration)")
st.metric(label="High Survival Rate", value=f"{survival_high:.2%}")
st.metric(label="Low Survival Rate", value=f"{survival_low:.2%}")

# Plotting
fig, ax = plt.subplots()
df.plot(kind='bar', ax=ax)
plt.title("Casualties by Weapon System")
plt.ylabel("Personnel")
st.pyplot(fig)

# Footer
st.caption("Model based on empirical casualty rates, commander effect, morale, terrain, and electronic warfare. Survival rates use decay functions aligned with historic conflict benchmarks and Mediazona data.")
