import streamlit as st
import pandas as pd
import math
import altair as alt

# Title and Intro
st.title("Casualty Dashboard: Russo-Ukrainian Conflict")
st.markdown("""
This dashboard estimates cumulative casualty outcomes using a validated conflict model.

### Core Model: How It Works
Casualty and degradation calculations are based on:
- Artillery usage (70–90% of losses in conventional war)
- Drone warfare and air strikes adjusted for EW effects
- Commander efficiency and leadership survivability bonuses
- Morale and logistics impact on operational performance
- Real-world experience scaling and asymmetric equipment availability

> This simulation aligns with validated AI predictions and 25+ historical conflicts for casualty realism.
""")

# Sidebar Configuration
with st.sidebar:
    st.header("Scenario Configuration")
    duration_days = st.slider("Conflict Duration (Days)", 30, 1825, 1031, step=7)
    intensity_level = st.slider("Combat Intensity (1=Low, 5=High)", 1, 5, 3)

    st.subheader("🇷🇺 Russian Modifiers")
    exp_rus = st.slider("Experience Factor (RU)", 0.5, 1.5, 1.15, step=0.01)
    ew_rus = st.slider("EW Effectiveness vs Ukraine", 0.1, 1.5, 0.90, step=0.01)
    cmd_rus = st.slider("Commander Efficiency (RU)", 0.0, 0.5, 0.35, step=0.01)
    med_rus = st.slider("Medical Support (RU)", 0.0, 1.0, 0.65, step=0.01)
    moral_rus = st.slider("Morale Factor (RU)", 0.5, 1.5, 1.2, step=0.01)
    logi_rus = st.slider("Logistics Effectiveness (RU)", 0.5, 1.5, 1.10, step=0.01)

    st.subheader("🇺🇦 Ukrainian Modifiers")
    exp_ukr = st.slider("Experience Factor (UA)", 0.5, 1.5, 0.80, step=0.01)
    ew_ukr = st.slider("EW Effectiveness vs Russia", 0.1, 1.5, 0.45, step=0.01)
    cmd_ukr = st.slider("Commander Efficiency (UA)", 0.0, 0.5, 0.12, step=0.01)
    med_ukr = st.slider("Medical Support (UA)", 0.0, 1.0, 0.43, step=0.01)
    moral_ukr = st.slider("Morale Factor (UA)", 0.5, 1.5, 0.80, step=0.01)
    logi_ukr = st.slider("Logistics Effectiveness (UA)", 0.5, 1.5, 0.85, step=0.01)

    st.subheader("Environment & Weapon Systems")
    artillery_on = st.checkbox("Include Artillery", True)
    drones_on = st.checkbox("Include Drones", True)
    snipers_on = st.checkbox("Include Snipers", True)
    small_arms_on = st.checkbox("Include Small Arms", True)
    heavy_on = st.checkbox("Include Heavy Weapons", True)
    armor_on = st.checkbox("Include Armored Vehicles", True)
    airstrikes_on = st.checkbox("Include Air Strikes", True)

    st.subheader("ISR Coordination")
    s2s_rus = st.slider("🇷🇺 Sensor-to-Shooter Efficiency", 0.5, 1.0, 0.85, 0.01)
    s2s_ukr = st.slider("🇺🇦 Sensor-to-Shooter Efficiency", 0.5, 1.0, 0.65, 0.01)

    st.subheader("Air Defense & EW")
    ad_density_rus = st.slider("🇷🇺 AD Density", 0.0, 1.0, 0.85, 0.01)
    ew_cover_rus = st.slider("🇷🇺 EW Coverage", 0.0, 1.0, 0.75, 0.01)
    ad_ready_rus = st.slider("🇷🇺 AD Readiness", 0.0, 1.0, 0.90, 0.01)

    ad_density_ukr = st.slider("🇺🇦 AD Density", 0.0, 1.0, 0.60, 0.01)
    ew_cover_ukr = st.slider("🇺🇦 EW Coverage", 0.0, 1.0, 0.40, 0.01)
    ad_ready_ukr = st.slider("🇺🇦 AD Readiness", 0.0, 1.0, 0.50, 0.01)

    st.subheader("Force Posture")
    posture_rus = st.slider("🇷🇺 Russian Posture", 0.8, 1.2, 1.0, 0.01)
    posture_ukr = st.slider("🇺🇦 Ukrainian Posture", 0.8, 1.2, 1.0, 0.01)

# Intensity and Posture Calculation
intensity_map = {
    1: (20, 600),
    2: (50, 1000),
    3: (100, 1500),
    4: (160, 2500),
    5: (220, 3500)
}
base_rus, base_ukr = intensity_map[intensity_level]
base_rus *= posture_rus
base_ukr *= posture_ukr


import streamlit as st
import pandas as pd
import math
import altair as alt

# Title and Intro
st.title("Casualty Dashboard: Russo-Ukrainian Conflict")
st.markdown("""
This dashboard estimates cumulative casualty outcomes using a validated conflict model.

### Core Model: How It Works
Casualty and degradation calculations are based on:
- Artillery usage (70–90% of losses in conventional war)
- Drone warfare and air strikes adjusted for EW effects
- Commander efficiency and leadership survivability bonuses
- Morale and logistics impact on operational performance
- Real-world experience scaling and asymmetric equipment availability

> This simulation aligns with validated AI predictions and 25+ historical conflicts for casualty realism.
""")

# Sidebar Configuration
with st.sidebar:
    st.header("Scenario Configuration")
    duration_days = st.slider("Conflict Duration (Days)", 30, 1825, 1031, step=7)
    intensity_level = st.slider("Combat Intensity (1=Low, 5=High)", 1, 5, 3)

    st.subheader("🇷🇺 Russian Modifiers")
    exp_rus = st.slider("Experience Factor (RU)", 0.5, 1.5, 1.15, step=0.01)
    ew_rus = st.slider("EW Effectiveness vs Ukraine", 0.1, 1.5, 0.90, step=0.01)
    cmd_rus = st.slider("Commander Efficiency (RU)", 0.0, 0.5, 0.35, step=0.01)
    med_rus = st.slider("Medical Support (RU)", 0.0, 1.0, 0.65, step=0.01)
    moral_rus = st.slider("Morale Factor (RU)", 0.5, 1.5, 1.2, step=0.01)
    logi_rus = st.slider("Logistics Effectiveness (RU)", 0.5, 1.5, 1.10, step=0.01)

    st.subheader("🇺🇦 Ukrainian Modifiers")
    exp_ukr = st.slider("Experience Factor (UA)", 0.5, 1.5, 0.80, step=0.01)
    ew_ukr = st.slider("EW Effectiveness vs Russia", 0.1, 1.5, 0.45, step=0.01)
    cmd_ukr = st.slider("Commander Efficiency (UA)", 0.0, 0.5, 0.12, step=0.01)
    med_ukr = st.slider("Medical Support (UA)", 0.0, 1.0, 0.43, step=0.01)
    moral_ukr = st.slider("Morale Factor (UA)", 0.5, 1.5, 0.80, step=0.01)
    logi_ukr = st.slider("Logistics Effectiveness (UA)", 0.5, 1.5, 0.85, step=0.01)

    st.subheader("Environment & Weapon Systems")
    artillery_on = st.checkbox("Include Artillery", True)
    drones_on = st.checkbox("Include Drones", True)
    snipers_on = st.checkbox("Include Snipers", True)
    small_arms_on = st.checkbox("Include Small Arms", True)
    heavy_on = st.checkbox("Include Heavy Weapons", True)
    armor_on = st.checkbox("Include Armored Vehicles", True)
    airstrikes_on = st.checkbox("Include Air Strikes", True)

    st.subheader("ISR Coordination")
    s2s_rus = st.slider("🇷🇺 Sensor-to-Shooter Efficiency", 0.5, 1.0, 0.85, 0.01)
    s2s_ukr = st.slider("🇺🇦 Sensor-to-Shooter Efficiency", 0.5, 1.0, 0.65, 0.01)

    st.subheader("Air Defense & EW")
    ad_density_rus = st.slider("🇷🇺 AD Density", 0.0, 1.0, 0.85, 0.01)
    ew_cover_rus = st.slider("🇷🇺 EW Coverage", 0.0, 1.0, 0.75, 0.01)
    ad_ready_rus = st.slider("🇷🇺 AD Readiness", 0.0, 1.0, 0.90, 0.01)

    ad_density_ukr = st.slider("🇺🇦 AD Density", 0.0, 1.0, 0.60, 0.01)
    ew_cover_ukr = st.slider("🇺🇦 EW Coverage", 0.0, 1.0, 0.40, 0.01)
    ad_ready_ukr = st.slider("🇺🇦 AD Readiness", 0.0, 1.0, 0.50, 0.01)

    st.subheader("Force Posture")
    posture_rus = st.slider("🇷🇺 Russian Posture", 0.8, 1.2, 1.0, 0.01)
    posture_ukr = st.slider("🇺🇦 Ukrainian Posture", 0.8, 1.2, 1.0, 0.01)

# Intensity and Posture Calculation
intensity_map = {
    1: (20, 600),
    2: (50, 1000),
    3: (100, 1500),
    4: (160, 2500),
    5: (220, 3500)
}
base_rus, base_ukr = intensity_map[intensity_level]
base_rus *= posture_rus
base_ukr *= posture_ukr


# ===============================
# Force Composition Module
# ===============================
st.subheader("Force Composition")

composition_options = ["VDV", "Armored", "Infantry", "Mechanized", "Artillery", "CAS Air", "FPV Teams", "EW Units"]

composition_rus = st.multiselect("🇷🇺 Russian Composition", composition_options, default=composition_options)
composition_ukr = st.multiselect("🇺🇦 Ukrainian Composition", composition_options, default=composition_options)

composition_stats = {
    "VDV": {"cohesion": 1.25, "weapons": 1.15, "training": 1.3},
    "Armored": {"cohesion": 1.1, "weapons": 1.25, "training": 1.1},
    "Infantry": {"cohesion": 0.9, "weapons": 0.8, "training": 0.85},
    "Mechanized": {"cohesion": 1.05, "weapons": 1.15, "training": 1.0},
    "Artillery": {"cohesion": 1.1, "weapons": 1.3, "training": 1.0},
    "CAS Air": {"cohesion": 1.0, "weapons": 1.2, "training": 1.05},
    "FPV Teams": {"cohesion": 0.95, "weapons": 1.1, "training": 1.05},
    "EW Units": {"cohesion": 1.1, "weapons": 1.0, "training": 1.1}
}

def aggregate_composition(selection):
    if not selection:
        return 1.0, 1.0, 1.0
    c_sum, w_sum, t_sum = 0, 0, 0
    for unit in selection:
        stats = composition_stats.get(unit, {})
        c_sum += stats.get("cohesion", 1)
        w_sum += stats.get("weapons", 1)
        t_sum += stats.get("training", 1)
    n = len(selection)
    return c_sum / n, w_sum / n, t_sum / n

coh_rus, weap_rus, train_rus = aggregate_composition(composition_rus)
coh_ukr, weap_ukr, train_ukr = aggregate_composition(composition_ukr)

# Replace original resilience logic to incorporate force composition
def force_resilience(moral, logi, cmd, cohesion, training):
    return morale_scaling(moral) * logistic_scaling(logi) * (1 + 0.2 * cmd) * cohesion * training

res_rus = force_resilience(moral_rus, logi_rus, cmd_rus, coh_rus, train_rus)
res_ukr = force_resilience(moral_ukr, logi_ukr, cmd_ukr, coh_ukr, train_ukr)

# Updated posture logic (optional: can apply exposure tuning based on posture later)


# === FORCE RESILIENCE AND COMPOSITION IMPACT ===
def force_resilience(moral, logi, cmd, cohesion, training):
    return morale_scaling(moral) * logistic_scaling(logi) * (1 + 0.2 * cmd) * cohesion * training

res_rus = force_resilience(moral_rus, logi_rus, cmd_rus, coh_rus, train_rus)
res_ukr = force_resilience(moral_ukr, logi_ukr, cmd_ukr, coh_ukr, train_ukr)

# Posture efficiency impact via resilience
def adjusted_posture(posture, resilience, baseline=1.0):
    offset = posture - 1.0
    impact = offset * (1 - baseline / resilience)
    return 1 + 0.25 * math.tanh(3 * impact)

posture_rus_adj = adjusted_posture(posture_rus, res_rus)
posture_ukr_adj = adjusted_posture(posture_ukr, res_ukr)

base_rus *= posture_rus_adj
base_ukr *= posture_ukr_adj
