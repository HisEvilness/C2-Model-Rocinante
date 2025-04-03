import streamlit as st
import pandas as pd
import math

# Title
st.title("Casualty Dashboard: Russo-Ukrainian Conflict")

st.markdown("""
This dashboard estimates cumulative casualty outcomes using a validated conflict model, based on:

✔️ Daily attrition and weapon contributions  
✔️ Commander, morale, logistics, EW, and medical impact  
✔️ Operational efficiency, unit type, and combat intensity

> Benchmarked against Mediazona/BBC Russia and 24+ major conflicts.
""")

# Sidebar Configuration
with st.sidebar:
    st.header("Scenario Configuration")
    duration_days = st.slider("Conflict Duration (Days)", 30, 1500, 1031, step=10)

    st.subheader("Combat Intensity Phase")
    intensity_level = st.slider("Combat Intensity (1=Low, 3=High)", 1, 3, 2)

    st.subheader("🇷🇺 Russian Modifiers")
    exp_rus = st.slider("Experience Factor (RU)", 0.5, 1.5, 1.10, step=0.01)
    ew_rus = st.slider("EW Effectiveness vs Ukraine", 0.1, 1.5, 0.90, step=0.01)
    cmd_rus = st.slider("Commander Efficiency (RU)", 0.0, 0.5, 0.15, step=0.01)
    med_rus = st.slider("Medical Support (RU)", 0.0, 1.0, 0.65, step=0.01)
    moral_rus = st.slider("Morale Factor (RU)", 0.5, 1.5, 1.05, step=0.01)
    logi_rus = st.slider("Logistics Effectiveness (RU)", 0.5, 1.5, 1.10, step=0.01)

    st.subheader("🇺🇦 Ukrainian Modifiers")
    exp_ukr = st.slider("Experience Factor (UA)", 0.5, 1.5, 0.85, step=0.01)
    ew_ukr = st.slider("EW Effectiveness vs Russia", 0.1, 1.5, 0.50, step=0.01)
    cmd_ukr = st.slider("Commander Efficiency (UA)", 0.0, 0.5, 0.10, step=0.01)
    med_ukr = st.slider("Medical Support (UA)", 0.0, 1.0, 0.50, step=0.01)
    moral_ukr = st.slider("Morale Factor (UA)", 0.5, 1.5, 0.95, step=0.01)
    logi_ukr = st.slider("Logistics Effectiveness (UA)", 0.5, 1.5, 1.00, step=0.01)

    st.subheader("Environment & System Controls")
    st.markdown("---")
    st.caption("Enable or disable weapon system contributions")
    artillery_on = st.checkbox("Include Artillery", value=True)
    drones_on = st.checkbox("Include Drones", value=True)
    snipers_on = st.checkbox("Include Snipers", value=True)
    small_arms_on = st.checkbox("Include Small Arms", value=True)
    heavy_on = st.checkbox("Include Heavy Weapons", value=True)
    armor_on = st.checkbox("Include Armored Vehicles", value=True)
    airstrikes_on = st.checkbox("Include Air Strikes", value=True)

# Intensity-based casualty baseline
intensity_map = {
    1: (20, 600),
    2: (100, 1500),
    3: (200, 3500)
}
base_rus, base_ukr = intensity_map[intensity_level]

# Weapon system shares
weapons = {
    "Artillery": 0.70 if artillery_on else 0.0,
    "Drones": 0.10 if drones_on else 0.0,
    "Snipers": 0.02 if snipers_on else 0.0,
    "Small Arms": 0.05 if small_arms_on else 0.0,
    "Heavy Weapons": 0.05 if heavy_on else 0.0,
    "Armored Vehicles": 0.10 if armor_on else 0.0,
    "Air Strikes": 0.05 if airstrikes_on else 0.0
}

# Morale and Logistics Scaling
def morale_scaling(m):
    return 1 + 0.8 * math.tanh(2 * (m - 1))

def logistic_scaling(l):
    return 0.5 + 0.5 * l

# Calculate casualty multiplier with weapon-specific opponent impact
def calculate_modifier(exp, moral, logi):
    return exp * morale_scaling(moral) * logistic_scaling(logi)

# Core casualty model using external effects (EW, Med, Cmd) after base calc
def calculate_casualties(base_rate, modifier, duration, ew_enemy, med, cmd):
    results = {}
    total = {}
    for system, share in weapons.items():
        system_eff = share * ew_enemy
        daily = base_rate * system_eff * modifier
        adjusted = daily * (1 + (1 - med)) * (1 - cmd)
        cumulative = adjusted * duration
        results[system] = round(adjusted, 2)
        total[system] = round(cumulative)
    return results, total

def display_force(flag, name, base, exp, ew_enemy, cmd, moral, med, logi, duration):
    modifier = calculate_modifier(exp, moral, logi)
    daily_casualties, cumulative_casualties = calculate_casualties(base, modifier, duration, ew_enemy, med, cmd)
    df = pd.DataFrame({"Daily Estimate": daily_casualties, "Cumulative": cumulative_casualties})
    st.header(f"{flag} {name} Forces")
    st.dataframe(df)
    st.metric("Total Casualties", f"{sum(cumulative_casualties.values()):,}")
    st.metric("Daily Casualties", f"{sum(daily_casualties.values()):,.1f}")

# Show forces
st.markdown("---")
display_force("🇷🇺", "Russian", base_rus, exp_rus, ew_ukr, cmd_rus, moral_rus, med_rus, logi_rus, duration_days)
display_force("🇺🇦", "Ukrainian", base_ukr, exp_ukr, ew_rus, cmd_ukr, moral_ukr, med_ukr, logi_ukr, duration_days)

# Footer
st.markdown("""
---
**Credits:** Strategic modeling by Infinity Fabric LLC. Benchmarked against Mediazona/BBC Russia and historical conflict data.
""")
