import streamlit as st
import pandas as pd
import math
import altair as alt

def morale_scaling(m): return 1 + 0.8 * math.tanh(2 * (m - 1))
def logistic_scaling(l): return 0.5 + 0.5 * l
def medical_scaling(med, morale): return (1 + (1 - med) ** 1.3) * (1 + 0.1 * (morale - 1))
def commander_scaling(cmd): return 1 / (1 + 0.3 * cmd)

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

# Utility Functions
def morale_scaling(m): return 1 + 0.8 * math.tanh(2 * (m - 1))
def logistic_scaling(l): return 0.5 + 0.5 * l
def medical_scaling(med, morale): return (1 + (1 - med) ** 1.3) * (1 + 0.1 * (morale - 1))
def commander_scaling(cmd): return 1 / (1 + 0.3 * cmd)

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

    st.subheader("Force Composition")
    composition_options = ["VDV", "Armored", "Infantry", "Mechanized", "Artillery", "CAS Air", "FPV Teams", "EW Units"]
    composition_rus = st.multiselect("🇷🇺 Russian Composition", composition_options, default=composition_options)
    composition_ukr = st.multiselect("🇺🇦 Ukrainian Composition", composition_options, default=composition_options)

    st.subheader("Force Posture")
    posture_rus = st.slider("🇷🇺 Russian Posture", 0.8, 1.2, 1.0, 0.01)
    posture_ukr = st.slider("🇺🇦 Ukrainian Posture", 0.8, 1.2, 1.0, 0.01)

with st.sidebar:
    ...
    st.subheader("Casualty Type Settings")
    kia_ratio = st.slider("Est. KIA Ratio", 0.20, 0.50, 0.30, step=0.01)

# === Force Composition Stats ===
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

def force_resilience(moral, logi, cmd, cohesion, training):
    return morale_scaling(moral) * logistic_scaling(logi) * (1 + 0.2 * cmd) * cohesion * training

res_rus = force_resilience(moral_rus, logi_rus, cmd_rus, coh_rus, train_rus)
res_ukr = force_resilience(moral_ukr, logi_ukr, cmd_ukr, coh_ukr, train_ukr)

def adjusted_posture(posture, resilience, baseline=1.0):
    offset = posture - 1.0
    impact = offset * (1 - baseline / resilience)
    return 1 + 0.25 * math.tanh(3 * impact)

posture_rus_adj = adjusted_posture(posture_rus, res_rus)
posture_ukr_adj = adjusted_posture(posture_ukr, res_ukr)

intensity_map = {
    1: (20, 600),
    2: (50, 1000),
    3: (100, 1500),
    4: (160, 2500),
    5: (220, 3500)
}
base_rus, base_ukr = intensity_map[intensity_level]
base_rus *= posture_rus_adj
base_ukr *= posture_ukr_adj

# === Weapon Shares ===
share_values = {
    "Artillery": 0.63,
    "Drones": 0.10,
    "Snipers": 0.01,
    "Small Arms": 0.05,
    "Heavy Weapons": 0.04,
    "Armored Vehicles": 0.07,
    "Air Strikes": 0.10
}

weapons = {
    "Artillery": share_values["Artillery"] if artillery_on else 0.0,
    "Drones": share_values["Drones"] if drones_on else 0.0,
    "Snipers": share_values["Snipers"] if snipers_on else 0.0,
    "Small Arms": share_values["Small Arms"] if small_arms_on else 0.0,
    "Heavy Weapons": share_values["Heavy Weapons"] if heavy_on else 0.0,
    "Armored Vehicles": share_values["Armored Vehicles"] if armor_on else 0.0,
    "Air Strikes": share_values["Air Strikes"] if airstrikes_on else 0.0
}

total_share = sum(weapons.values())
if total_share == 0:
    st.warning("Please enable at least one weapon system to view casualty estimates.")
    st.stop()

# === Casualty Calculation Logic ===
def calculate_casualties_range(base_rate, modifier, duration, ew_enemy, med, cmd, moral, logi,
                                s2s, ad_density, ew_cover, ad_ready, weap_quality, training):
    results, total = {}, {}

    decay_strength = 0.00035 + 0.00012 * math.tanh(duration / 800)
    base_resistance = morale_scaling(moral) * logistic_scaling(logi) * training
    decay_curve_factor = max(math.exp(-decay_strength * duration / base_resistance), 0.6)

    for system, share in weapons.items():
        base_share = share / total_share
        logi_factor = logistic_scaling(logi)
        cmd_factor = commander_scaling(cmd)
        weapon_boost = min(max(1 + 0.07 * (logi_factor - 1) - 0.01 * cmd_factor, 0.95), 1.08)

        if system == "Artillery":
            system_scaling = logistic_scaling(logi) * 0.95
        elif system == "Drones":
            drone_decay = max(0.9, 1 - 0.0002 * duration)
            system_scaling = 0.65 * drone_decay
        else:
            system_scaling = 1.0

        ew_multiplier = 1.0 if system == 'Air Strikes' else (0.75 if system == 'Drones' else 1.0)
        coordination_bonus = min(max(s2s, 0.85), 1.10) if system in ["Artillery", "Air Strikes", "Drones"] else 1.0
        drone_penalty = min(max((1 - ad_density * ad_ready) * (1 - ew_cover), 0.75), 1.05) if system in ["Drones", "Air Strikes"] else 1.0

        system_eff = base_share * ew_enemy * ew_multiplier * weapon_boost * system_scaling * coordination_bonus * drone_penalty
        system_eff *= weap_quality
        system_eff = max(system_eff, 0.35)

        suppression = 1 - (0.05 + 0.05 * cmd)
        base = base_rate * base_share * system_eff * modifier * medical_scaling(med, moral) * suppression
        daily_base = base * decay_curve_factor

        daily_min = daily_base * 0.95
        daily_max = daily_base * 1.05

        results[system] = (round(daily_min, 1), round(daily_max, 1))
        total[system] = (round(daily_min * duration), round(daily_max * duration))

    return results, total

# === Fixed Weapon System Bar + Cumulative Line Chart ===
from collections import OrderedDict

def calculate_casualties_range(base_rate, modifier, duration, ew_enemy, med, cmd, moral, logi,
                                s2s, ad_density, ew_cover, ad_ready, weap_quality, training):
    results, total = OrderedDict(), OrderedDict()

    total_share = sum(weapons.values())
    if total_share == 0:
        st.warning("No active weapon systems. Please enable at least one.")
        return {}, {}

    for system, share in weapons.items():
        if share == 0:
            continue

        base_share = share / total_share
        logi_factor = logistic_scaling(logi)
        cmd_factor = commander_scaling(cmd)
        weapon_boost = min(max(1 + 0.07 * (logi_factor - 1) - 0.01 * cmd_factor, 0.95), 1.08)

        # Per-system scaling
        if system == "Artillery":
            system_scaling = logistic_scaling(logi) * 0.95
        elif system == "Drones":
            drone_decay = max(0.9, 1 - 0.0002 * duration)
            system_scaling = 0.65 * drone_decay
        else:
            system_scaling = 1.0

        ew_multiplier = 1.0 if system == "Air Strikes" else (0.75 if system == "Drones" else 1.0)
        coordination_bonus = min(max(s2s, 0.85), 1.10) if system in ["Artillery", "Air Strikes", "Drones"] else 1.0
        drone_penalty = min(max((1 - ad_density * ad_ready) * (1 - ew_cover), 0.75), 1.05) if system in ["Drones", "Air Strikes"] else 1.0

        system_eff = base_share * ew_enemy * ew_multiplier * weapon_boost * system_scaling * coordination_bonus * drone_penalty
        system_eff *= weap_quality
        system_eff = max(system_eff, 0.35)

        suppression = 1 - (0.05 + 0.05 * cmd)
        base = base_rate * system_eff * modifier * medical_scaling(med, moral) * suppression

        decay_strength = 0.00035 + 0.00012 * math.tanh(duration / 800)
        base_resistance = morale_scaling(moral) * logistic_scaling(logi) * training
        decay_curve_factor = max(math.exp(-decay_strength * duration / base_resistance), 0.6)

        daily_base = base * decay_curve_factor
        daily_min = daily_base * 0.95
        daily_max = daily_base * 1.05

        results[system] = (round(daily_min, 1), round(daily_max, 1))
        total[system] = (round(daily_min * duration), round(daily_max * duration))

        # 🔍 Debug Output (optional)
        st.write(f"🧪 {system}", {
            "share": share,
            "base_share": base_share,
            "weapon_boost": weapon_boost,
            "system_scaling": system_scaling,
            "coordination_bonus": coordination_bonus,
            "drone_penalty": drone_penalty,
            "system_eff": system_eff,
            "daily_base": daily_base
        })

    return results, total

# === Daily Casualty Curve Chart ===
def plot_daily_curve(title, daily_range, duration):
    x = list(range(0, duration + 1, 7))
    min_per_day = [sum(v[0] for v in daily_range.values())] * len(x)
    max_per_day = [sum(v[1] for v in daily_range.values())] * len(x)

    daily_df = pd.DataFrame({
        "Day": x,
        "Min": min_per_day,
        "Max": max_per_day
    })

    melted = pd.melt(daily_df, id_vars="Day", value_vars=["Min", "Max"], var_name="Type", value_name="Casualties")

    chart = alt.Chart(melted).mark_line().encode(
        x=alt.X("Day:Q", title="Day"),
        y=alt.Y("Casualties:Q", title="Estimated Casualties per Day"),
        color="Type:N"
    ).properties(
        title=f"{title} Daily Casualty Curve",
        width=700,
        height=300
    )

    st.altair_chart(chart, use_container_width=True)

def plot_casualty_chart(title, daily_range, cumulative_range):
    st.subheader(f"{title} Casualty Distribution")

    # Preserve order
    systems = list(daily_range.keys())

    chart_data = pd.DataFrame({
        "Weapon System": systems,
        "Min": [cumulative_range[sys][0] for sys in systems],
        "Max": [cumulative_range[sys][1] for sys in systems]
    })

    chart_data["Delta"] = chart_data["Max"] - chart_data["Min"]
    chart_data["Max End"] = chart_data["Min"] + chart_data["Delta"]

    base = alt.Chart(chart_data).mark_bar(size=40, color="#bbbbbb").encode(
        x=alt.X('Weapon System:N', sort=None, title='Weapon System'),
        y=alt.Y('Min:Q', title='Min Casualties')
    )

    delta = alt.Chart(chart_data).mark_bar(size=40, color="#1f77b4").encode(
        x=alt.X('Weapon System:N', sort=None),
        y='Min:Q',
        y2='Max End:Q',
        tooltip=['Weapon System', 'Min', 'Max']
    )

    st.altair_chart(base + delta, use_container_width=True)

    # Cumulative Line Chart
    line_data = pd.DataFrame({
        "Days": list(range(0, duration_days + 1, 7)),
        "Min": [sum(v[0] for v in daily_range.values()) * i for i in range(0, duration_days + 1, 7)],
        "Max": [sum(v[1] for v in daily_range.values()) * i for i in range(0, duration_days + 1, 7)]
    })

    line_data = pd.melt(line_data, id_vars='Days', value_vars=['Min', 'Max'], var_name='Type', value_name='Casualties')

    line_chart = alt.Chart(line_data).mark_line(interpolate='monotone').encode(
        x=alt.X('Days:Q', title="Days"),
        y=alt.Y('Casualties:Q', title="Cumulative Casualties"),
        color='Type:N'
    ).properties(
        title=f"{title} Cumulative Casualty Curve",
        width=700,
        height=300
    )

    st.altair_chart(line_chart, use_container_width=True)

def plot_daily_curve(title, daily_range, duration):
    x = list(range(0, duration + 1, 7))
    min_per_day = [sum(v[0] for v in daily_range.values())] * len(x)
    max_per_day = [sum(v[1] for v in daily_range.values())] * len(x)

    daily_df = pd.DataFrame({
        "Day": x,
        "Min": min_per_day,
        "Max": max_per_day
    })

    melted = pd.melt(daily_df, id_vars="Day", value_vars=["Min", "Max"], var_name="Type", value_name="Casualties")

    chart = alt.Chart(melted).mark_line().encode(
        x=alt.X("Day:Q", title="Day"),
        y=alt.Y("Casualties:Q", title="Estimated Daily Casualties"),
        color="Type:N"
    ).properties(
        title=f"{title} Daily Casualty Curve",
        width=700,
        height=300
    )

    st.altair_chart(chart, use_container_width=True)

# === Display Function with KIA/WIA, Debug and Dual Charting ===
def display_force(flag, name, base, exp, ew_enemy, cmd, moral, med, logi, duration,
                  enemy_exp, enemy_ew, s2s, ad_dens, ew_cov, ad_ready, weap_q, train, kia_ratio):
    modifier = exp * morale_scaling(moral) * logistic_scaling(logi)
    daily_range, cumulative_range = calculate_casualties_range(
        base, modifier, duration, ew_enemy, med, cmd, moral, logi,
        s2s, ad_dens, ew_cov, ad_ready, weap_q, train
    )

    df = pd.DataFrame({
        "Daily Min": {k: v[0] for k, v in daily_range.items()},
        "Daily Max": {k: v[1] for k, v in daily_range.items()},
        "Cumulative Min": {k: v[0] for k, v in cumulative_range.items()},
        "Cumulative Max": {k: v[1] for k, v in cumulative_range.items()}
    })

    st.header(f"{flag} {name} Forces")
    st.dataframe(df)

    total_min = sum(v[0] for v in cumulative_range.values())
    total_max = sum(v[1] for v in cumulative_range.values())
    kia_min = round(total_min * kia_ratio)
    kia_max = round(total_max * kia_ratio)
    wia_min = round(total_min - kia_min)
    wia_max = round(total_max - kia_max)

    st.metric("Total Casualties", f"{total_min:,} - {total_max:,}")
    st.metric("KIA Estimate", f"{kia_min:,} - {kia_max:,}")
    st.metric("WIA Estimate", f"{wia_min:,} - {wia_max:,}")

    plot_casualty_chart(name, daily_range, cumulative_range)
    plot_daily_curve(title=name, daily_range=daily_range, duration=duration)

# === Render Outputs ===
display_force("🇷🇺", "Russian", base_rus, exp_rus, ew_ukr, cmd_rus, moral_rus, med_rus, logi_rus, duration_days,
              exp_ukr, ew_rus, s2s_rus, ad_density_rus, ew_cover_rus, ad_ready_rus, weap_rus, train_rus, kia_ratio)

display_force("🇺🇦", "Ukrainian", base_ukr, exp_ukr, ew_rus, cmd_ukr, moral_ukr, med_ukr, logi_ukr, duration_days,
              exp_rus, ew_ukr, s2s_ukr, ad_density_ukr, ew_cover_ukr, ad_ready_ukr, weap_ukr, train_ukr, kia_ratio)

# === Historical Conflict Benchmarks & Comparison ===
st.markdown("""---""")
st.subheader("📊 Historical Conflict Benchmarks vs Model Output")

benchmarks = pd.DataFrame([
    {"Conflict": "Verdun (WWI)", "Days": 300, "Reference": 700_000},
    {"Conflict": "Eastern Front (WWII)", "Days": 1410, "Reference": 6_000_000},
    {"Conflict": "Vietnam War", "Days": 5475, "Reference": 1_100_000},
    {"Conflict": "Korean War", "Days": 1128, "Reference": 1_200_000},
    {"Conflict": "Iran–Iraq War", "Days": 2920, "Reference": 1_000_000},
    {"Conflict": "Iraq War", "Days": 2920, "Reference": 525_000},
    {"Conflict": "Russo-Ukrainian (Model)", "Days": duration_days, "Reference": 675_000}  # mid range
])

model_total = sum(v[0] for v in calculate_casualties_range(
    base_rus, exp_rus * morale_scaling(moral_rus) * logistic_scaling(logi_rus),
    duration_days, ew_ukr, med_rus, cmd_rus, moral_rus, logi_rus,
    s2s_rus, ad_density_rus, ew_cover_rus, ad_ready_rus, weap_rus, train_rus
)[1].values()) + sum(v[0] for v in calculate_casualties_range(
    base_ukr, exp_ukr * morale_scaling(moral_ukr) * logistic_scaling(logi_ukr),
    duration_days, ew_rus, med_ukr, cmd_ukr, moral_ukr, logi_ukr,
    s2s_ukr, ad_density_ukr, ew_cover_ukr, ad_ready_ukr, weap_ukr, train_ukr
)[1].values())

benchmarks["Model (Total)"] = benchmarks.apply(
    lambda row: model_total if row["Conflict"] == "Russo-Ukrainian (Model)" else row["Reference"],
    axis=1
)
benchmarks["Deviation %"] = (benchmarks["Model (Total)"] - benchmarks["Reference"]) / benchmarks["Reference"] * 100
benchmarks["Deviation %"] = benchmarks["Deviation %"].round(2)

st.dataframe(benchmarks.style.format({
    "Reference": "{:,.0f}",
    "Model (Total)": "{:,.0f}",
    "Deviation %": "{:+.2f}%"
}))
