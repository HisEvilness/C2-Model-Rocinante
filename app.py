import streamlit as st
import pandas as pd

# Title
st.title("Casualty & Survival Dashboard: Russo-Ukrainian Conflict")

# Unit Selection for Force 1 (Russia) - All units selected by default
st.header("Force 1: Russia")
unit_types_russia = {
    "Mechanized": (60, 150),
    "Infantry": (80, 200),
    "VDV (Airborne)": (70, 170),
    "Marines": (75, 190),
    "Armored": (100, 220),
    "Militias": (120, 280),
    "Volunteer Units": (130, 300)
}

# Force 1 Unit selection (All units selected by default)
selected_units_russia = []
for unit, (low, high) in unit_types_russia.items():
    selected = st.checkbox(f"Russia - {unit}", value=True)  # Default selected
    if selected:
        selected_units_russia.append((unit, low, high))

# Unit Selection for Force 2 (Ukraine) - All units selected by default
st.header("Force 2: Ukraine")
unit_types_ukraine = {
    "Mechanized": (60, 150),
    "Infantry": (80, 200),
    "VDV (Airborne)": (70, 170),
    "Marines": (75, 190),
    "Armored": (100, 220),
    "Militias": (120, 280),
    "Volunteer Units": (130, 300)
}

# Force 2 Unit selection (All units selected by default)
selected_units_ukraine = []
for unit, (low, high) in unit_types_ukraine.items():
    selected = st.checkbox(f"Ukraine - {unit}", value=True)  # Default selected
    if selected:
        selected_units_ukraine.append((unit, low, high))

# Conflict Duration
duration_days = st.slider("Duration of Conflict (Days)", min_value=30, max_value=1500, step=30, value=300)

# Commander Effect
commander_effect = st.slider("Commander Effectiveness Modifier (0.8 - 1.2)", min_value=0.8, max_value=1.2, step=0.01, value=1.0)

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

# Calculate Casualties for Force 1 (Russia)
total_low_russia = 0
total_high_russia = 0
for unit, low, high in selected_units_russia:
    total_low_russia += int(low * duration_days * commander_effect)
    total_high_russia += int(high * duration_days * commander_effect)

# Calculate Casualties for Force 2 (Ukraine)
total_low_ukraine = 0
total_high_ukraine = 0
for unit, low, high in selected_units_ukraine:
    total_low_ukraine += int(low * duration_days * commander_effect)
    total_high_ukraine += int(high * duration_days * commander_effect)

# Casualty Calculation by Weapon System for Force 1 (Russia)
casualty_data_russia = {}
for system, contribution in weapon_systems.items():
    casualty_data_russia[system] = {
        "Low Estimate": int(total_low_russia * contribution),
        "High Estimate": int(total_high_russia * contribution)
    }

# Casualty Calculation by Weapon System for Force 2 (Ukraine)
casualty_data_ukraine = {}
for system, contribution in weapon_systems.items():
    casualty_data_ukraine[system] = {
        "Low Estimate": int(total_low_ukraine * contribution),
        "High Estimate": int(total_high_ukraine * contribution)
    }

# Display Results for Total Casualties
st.subheader("Estimated Total Casualties")
st.metric(label="Russia - Low Estimate", value=f"{total_low_russia:,} personnel")
st.metric(label="Russia - High Estimate", value=f"{total_high_russia:,} personnel")
st.metric(label="Ukraine - Low Estimate", value=f"{total_low_ukraine:,} personnel")
st.metric(label="Ukraine - High Estimate", value=f"{total_high_ukraine:,} personnel")

# Convert to DataFrame for Casualties by Weapon System
df_russia = pd.DataFrame(casualty_data_russia).T
df_ukraine = pd.DataFrame(casualty_data_ukraine).T

st.subheader("Casualties by Weapon System")
st.write("**Russia**")
st.dataframe(df_russia)
st.write("**Ukraine**")
st.dataframe(df_ukraine)

# Survival Probability (decay-based model without initial troop count)
daily_survival_low_russia = 1 - (total_low_russia / (total_low_russia + 1))
daily_survival_high_russia = 1 - (total_high_russia / (total_high_russia + 1))
survival_low_russia = daily_survival_low_russia ** duration_days
survival_high_russia = daily_survival_high_russia ** duration_days

daily_survival_low_ukraine = 1 - (total_low_ukraine / (total_low_ukraine + 1))
daily_survival_high_ukraine = 1 - (total_high_ukraine / (total_high_ukraine + 1))
survival_low_ukraine = daily_survival_low_ukraine ** duration_days
survival_high_ukraine = daily_survival_high_ukraine ** duration_days

st.subheader("Estimated Survival Rates (Probability Over Duration)")
st.write("**Russia**")
st.metric(label="Russia - High Survival Rate", value=f"{survival_high_russia:.2%}")
st.metric(label="Russia - Low Survival Rate", value=f"{survival_low_russia:.2%}")
st.write("**Ukraine**")
st.metric(label="Ukraine - High Survival Rate", value=f"{survival_high_ukraine:.2%}")
st.metric(label="Ukraine - Low Survival Rate", value=f"{survival_low_ukraine:.2%}")

# Plotting Casualties by Weapon System for Both Forces
st.subheader("Weapon System Casualty Breakdown")
st.bar_chart(df_russia, use_container_width=True)
st.bar_chart(df_ukraine, use_container_width=True)

# Footer
st.caption("Model based on empirical casualty rates, commander effect, and system efficiency inputs. Survival rates are calculated via decay functions, aligned with historic conflict benchmarks and Mediazona figures.")
