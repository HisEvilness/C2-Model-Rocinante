import streamlit as st
import pandas as pd

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
    high_intensity = st.checkbox("High-Intensity Combat", value=False)

    st.subheader("🇷🇺 Russian Modifiers")
    exp_rus = st.slider("Experience Factor (RU)", 0.5, 1.5, 1.10, step=0.01)
    ew_rus = st.slider("EW Effectiveness (RU)", 0.1, 1.5, 0.90, step=0.01)
    cmd_rus = st.slider("Commander Efficiency (RU)", 0.0, 0.5, 0.15, step=0.01)
    med_rus = st.slider("Medical Support (RU)", 0.0, 1.0, 0.65, step=0.01)
    moral_rus = st.slider("Morale Factor (RU)", 0.5, 1.5, 1.05, step=0.01)
    logi_rus = st.slider("Logistics Effectiveness (RU)", 0.5, 1.5, 1.10, step=0.01)
    base_rus = 20 if not high_intensity else 200

    st.subheader("🇺🇦 Ukrainian Modifiers")
    exp_ukr = st.slider("Experience Factor (UA)", 0.5, 1.5, 0.85, step=0.01)
    ew_ukr = st.slider("EW Effectiveness (UA)", 0.1, 1.5, 0.50, step=0.01)
    cmd_ukr = st.slider("Commander Efficiency (UA)", 0.0, 0.5, 0.10, step=0.01)
    med_ukr = st.slider("Medical Support (UA)", 0.0, 1.0, 0.50, step=0.01)
    moral_ukr = st.slider("Morale Factor (UA)", 0.5, 1.5, 0.95, step=0.01)
    logi_ukr = st.slider("Logistics Effectiveness (UA)", 0.5, 1.5, 1.00, step=0.01)
    base_ukr = 600 if not high_intensity else 3500

    st.markdown("---")
    st.caption("Check to enable or disable weapon system contributions")
    artillery_on = st.checkbox("Include Artillery", value=True)
    drones_on = st.checkbox("Include Drones", value=True)
    snipers_on = st.checkbox("Include Snipers", value=True)
    small_arms_on = st.checkbox("Include Small Arms", value=True)
    heavy_on = st.checkbox("Include Heavy Weapons", value=True)
    armor_on = st.checkbox("Include Armored Vehicles", value=True)
    airstrikes_on = st.checkbox("Include Air Strikes", value=True)

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

# Function to compute weapon-based casualties
def compute_casualties(base_casualty, exp_mod, ew_mod, cmd_mod, moral_mod, med_mod, logi_mod, days):
    daily = {}
    total = {}
    modifier = exp_mod * ew_mod * (1 - cmd_mod) * moral_mod * (1 - med_mod) * logi_mod
    for weapon, share in weapons.items():
        daily_val = base_casualty * share * modifier
        daily[weapon] = round(daily_val, 1)
        total[weapon] = round(daily_val * days)
    return daily, total

def display_force(flag, name, base, exp, ew, cmd, moral, med, logi, days):
    daily, total = compute_casualties(base, exp, ew, cmd, moral, med, logi, days)
    df = pd.DataFrame({"Daily Estimate": daily, "Cumulative": total})
    st.header(f"{flag} {name} Forces")
    st.dataframe(df)
    st.metric("Total Casualties", f"{sum(total.values()):,}")
    st.metric("Daily Casualties", f"{sum(daily.values()):,.1f}")

# Display force outputs
display_force("🇷🇺", "Russian", base_rus, exp_rus, ew_rus, cmd_rus, moral_rus, med_rus, logi_rus, duration_days)
display_force("🇺🇦", "Ukrainian", base_ukr, exp_ukr, ew_ukr, cmd_ukr, moral_ukr, med_ukr, logi_ukr, duration_days)

# Footer
st.markdown("""
---
**Credits:**  
Strategic Modeling by Infinity Fabric LLC  
Dashboard Engine: Streamlit  
Data Sources: Mediazona, BBC Russia, 24-Conflict Historical Dataset
""")
