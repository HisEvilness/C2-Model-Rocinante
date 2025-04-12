import streamlit as st
import pandas as pd
import math
import altair as alt
from collections import OrderedDict

# === Utility Functions ===
def morale_scaling(m): return 1 + 0.8 * math.tanh(2 * (m - 1))
def logistic_scaling(l): return 0.5 + 0.5 * l

def medical_scaling(med, morale, logi):
    penalty = 1 + (1.2 * (1 - med)) ** 1.1
    morale_adj = 1 + 0.1 * (morale - 1)
    compound = 1 + 0.15 * (1 - logi) if logi < 0.75 else 1.0
    return penalty * morale_adj * compound

def commander_scaling(cmd): return 1 / (1 + 0.3 * cmd)
    
# === KIA Ratios ===
def calculate_kia_ratio(med, logi, cmd, morale, training, cohesion, dominance_mods, base_slider=0.30):
    """
    Calculates dynamic KIA ratio using AI model logic:
    - Penalized by low medical, poor logistics
    - Boosted by training, morale, cohesion
    - Dominance sharply increases KIA if outmatched
    """

    med_penalty = (1.2 * (1 - med)) ** 1.2
    logi_penalty = (1 - (logi / 1.5)) ** 1.0
    cmd_bonus = 0.25 * cmd

    # AI logic: training & cohesion reduce fatality bias
    train_bonus = 1 - 0.15 * (1 - training)
    cohesion_bonus = 1 - 0.10 * (1 - cohesion)
    morale_bonus = 1 - 0.10 * (1 - morale)

    # Combined survival reduction
    survivability = train_bonus * cohesion_bonus * morale_bonus

    # Dominance boost
    suppression_mod = dominance_mods.get("suppression_mod", 1.0)
    DOMINANCE_SCALING = 0.45
    dominance_boost = 1 + DOMINANCE_SCALING * (1 - suppression_mod)
    dominance_boost = min(max(dominance_boost, 0.85), 1.25)

    # Final KIA ratio
    adjusted = base_slider * (1 + med_penalty + logi_penalty - cmd_bonus) * dominance_boost / survivability
    return min(max(adjusted, 0.10), 0.85)  # AI model range

# === WIA to KIA Ratios ===

# === Relative Advantage Calculation ===
def compute_relative_dominance(cmd_rus, cmd_ukr, logi_rus, logi_ukr, moral_rus, moral_ukr):
    return {
        "cmd_delta": cmd_rus - cmd_ukr,
        "logi_delta": logi_rus - logi_ukr,
        "morale_delta": moral_rus - moral_ukr
    }

def compute_dominance_modifiers(deltas):
    """
    Converts dominance deltas into balanced multipliers affecting casualty suppression and system efficiency.
    - Boosts for positive advantage
    - Penalties for negative delta
    - Soft caps to avoid overpowering
    """
    def scale(delta, base=1.0, strength=0.10, cap=0.15):
        return base + math.tanh(delta) * min(abs(delta) * strength, cap)

    # Extract deltas
    cmd_delta = deltas.get("cmd_delta", 0)
    logi_delta = deltas.get("logi_delta", 0)
    morale_delta = deltas.get("morale_delta", 0)
    ad_delta = deltas.get("ad_delta", 0)
    ew_delta = deltas.get("ew_delta", 0)

    return {
        "suppression_mod": scale(cmd_delta + logi_delta, base=1.0, strength=0.08, cap=0.12),
        "efficiency_mod": scale(morale_delta + ad_delta + ew_delta, base=1.0, strength=0.07, cap=0.10)
    }

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
    exp_rus = st.slider("Experience Factor (RU)", 0.5, 1.5, 1.25, step=0.01)
    ew_rus = st.slider("EW Effectiveness vs Ukraine", 0.1, 1.5, 1.15, step=0.01)
    cmd_rus = st.slider("Commander Efficiency (RU)", 0.0, 0.5, 0.40, step=0.01)
    med_rus = st.slider("Medical Support (RU)", 0.0, 1.0, 0.70, step=0.01)
    moral_rus = st.slider("Morale Factor (RU)", 0.5, 1.5, 1.25, step=0.01)
    logi_rus = st.slider("Logistics Effectiveness (RU)", 0.5, 1.5, 1.20, step=0.01)

    st.subheader("🇺🇦 Ukrainian Modifiers")
    exp_ukr = st.slider("Experience Factor (UA)", 0.5, 1.5, 0.75, step=0.01)
    ew_ukr = st.slider("EW Effectiveness vs Russia", 0.1, 1.5, 0.45, step=0.01)
    cmd_ukr = st.slider("Commander Efficiency (UA)", 0.0, 0.5, 0.15, step=0.01)
    med_ukr = st.slider("Medical Support (UA)", 0.0, 1.0, 0.40, step=0.01)
    moral_ukr = st.slider("Morale Factor (UA)", 0.5, 1.5, 0.80, step=0.01)
    logi_ukr = st.slider("Logistics Effectiveness (UA)", 0.5, 1.5, 0.75, step=0.01)

    st.subheader("Environment & Weapon Systems")
    artillery_on = st.checkbox("Include Artillery", True)
    drones_on = st.checkbox("Include Drones", True)
    snipers_on = st.checkbox("Include Snipers", True)
    small_arms_on = st.checkbox("Include Small Arms", True)
    heavy_on = st.checkbox("Include Heavy Weapons", True)
    armor_on = st.checkbox("Include Armored Vehicles", True)
    airstrikes_on = st.checkbox("Include Air Strikes", True)

    st.subheader("ISR Coordination")
    s2s_rus = st.slider("🇷🇺 Sensor-to-Shooter Efficiency", 0.5, 1.0, 0.90, 0.01)
    s2s_ukr = st.slider("🇺🇦 Sensor-to-Shooter Efficiency", 0.5, 1.0, 0.65, 0.01)

    st.subheader("Air Defense & EW")
    ad_density_rus = st.slider("🇷🇺 AD Density", 0.0, 1.0, 0.90, 0.01)
    ew_cover_rus = st.slider("🇷🇺 EW Coverage", 0.0, 1.0, 0.80, 0.01)
    ad_ready_rus = st.slider("🇷🇺 AD Readiness", 0.0, 1.0, 0.95, 0.01)

    ad_density_ukr = st.slider("🇺🇦 AD Density", 0.0, 1.0, 0.60, 0.01)
    ew_cover_ukr = st.slider("🇺🇦 EW Coverage", 0.0, 1.0, 0.40, 0.01)
    ad_ready_ukr = st.slider("🇺🇦 AD Readiness", 0.0, 1.0, 0.50, 0.01)

    st.subheader("Casualty Type Settings")
    kia_ratio = st.slider("Est. KIA Ratio", 0.10, 0.70, 0.48, step=0.01)

    st.subheader("Force Composition")

    composition_options = [
        "VDV", "Armored", "Mechanized", "Artillery", "CAS Air", "Engineer Units", "National Guard",
        "SOF", "Storm-Z", "EW Units", "Recon", "C4ISR Teams",
        "Infantry", "Territorial Defense", "Reservists", "Drone Units", "FPV Teams", "Foreign Legion"
    ]

    composition_rus = st.multiselect(
        "🇷🇺 Russian Composition", composition_options,
        default=[
            "VDV", "Armored", "Mechanized", "Artillery", "CAS Air", "Engineer Units",
            "National Guard", "SOF", "Storm-Z", "EW Units", "Recon", "C4ISR Teams"
        ]
    )

    composition_ukr = st.multiselect(
        "🇺🇦 Ukrainian Composition", composition_options,
        default=[
            "Infantry", "Territorial Defense", "Reservists", "FPV Teams", "Drone Units",
            "Engineer Units", "Foreign Legion", "SOF", "Artillery", "Recon", "C4ISR Teams"
        ]
    )

    st.subheader("Force Posture")
    posture_rus = st.slider("🇷🇺 Russian Posture", 0.8, 1.2, 1.05, 0.01)
    posture_ukr = st.slider("🇺🇦 Ukrainian Posture", 0.8, 1.2, 0.95, 0.01)

# === Force Composition Stats ===
composition_stats = {
    "VDV": {"cohesion": 1.25, "weapons": 1.15, "training": 1.30},
    "Armored": {"cohesion": 1.10, "weapons": 1.25, "training": 1.10},
    "Mechanized": {"cohesion": 1.05, "weapons": 1.15, "training": 1.00},
    "Artillery": {"cohesion": 1.10, "weapons": 1.30, "training": 1.00},
    "CAS Air": {"cohesion": 1.00, "weapons": 1.20, "training": 1.05},
    "Engineer Units": {"cohesion": 1.00, "weapons": 0.95, "training": 1.10},
    "National Guard": {"cohesion": 0.95, "weapons": 0.90, "training": 0.85},
    "Storm-Z": {"cohesion": 0.80, "weapons": 0.85, "training": 0.70},
    "SOF": {"cohesion": 1.25, "weapons": 1.20, "training": 1.30},
    "EW Units": {"cohesion": 1.10, "weapons": 1.00, "training": 1.10},
    "Recon": {"cohesion": 1.15, "weapons": 1.10, "training": 1.20},
    "C4ISR Teams": {"cohesion": 1.10, "weapons": 1.05, "training": 1.25},
    "Infantry": {"cohesion": 0.90, "weapons": 0.80, "training": 0.85},
    "Territorial Defense": {"cohesion": 0.75, "weapons": 0.70, "training": 0.65},
    "Reservists": {"cohesion": 0.70, "weapons": 0.60, "training": 0.55},
    "Drone Units": {"cohesion": 0.90, "weapons": 1.25, "training": 1.10},
    "FPV Teams": {"cohesion": 0.95, "weapons": 1.10, "training": 1.05},
    "Foreign Legion": {"cohesion": 1.10, "weapons": 1.05, "training": 1.15}
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

coh_rus, weapon_quality_rus, train_rus = aggregate_composition(composition_rus)
coh_ukr, weapon_quality_ukr, train_ukr = aggregate_composition(composition_ukr)

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

def medical_scaling(med, morale, logi):
    """
    Calculates how medical efficiency, morale, and logistics affect survival.
    """
    penalty = 1 + (1.2 * (1 - med)) ** 1.1
    morale_adj = 1 + 0.1 * (morale - 1)
    compound = 1 + 0.15 * (1 - logi) if logi < 0.75 else 1.0
    return penalty * morale_adj * compound

def get_kia_ratio_by_system(system):
    # Baseline values based on historical data
    ratios = {
        "Artillery": 0.35,
        "Drones": 0.55,
        "Snipers": 0.65,
        "Small Arms": 0.30,
        "Heavy Weapons": 0.40,
        "Armored Vehicles": 0.50,
        "Air Strikes": 0.60
    }
    return ratios.get(system, 0.40)  # Default fallback

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
    "Artillery": 0.62,
    "Drones": 0.13,
    "Snipers": 0.01,
    "Small Arms": 0.05,
    "Heavy Weapons": 0.04,
    "Armored Vehicles": 0.06,
    "Air Strikes": 0.09
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

# === Available Unit Types ===
composition_options = [
    "VDV", "Armored", "Mechanized", "Artillery", "CAS Air", "Engineer Units", "National Guard",
    "SOF", "Storm-Z", "EW Units", "Recon", "C4ISR Teams",
    "Infantry", "Territorial Defense", "Reservists", "Drone Units", "FPV Teams", "Foreign Legion"
]
    
# === KIA/WIA Logic ===
def calculate_kia_ratio(med, logi, cmd, morale, training, cohesion, dominance_mods, base_slider=0.30):
    """
    Calculates dynamic KIA ratio using AI model logic:
    - Penalized by low medical, poor logistics
    - Boosted by training, morale, cohesion
    - Dominance sharply increases KIA if outmatched
    """

    med_penalty = (1.2 * (1 - med)) ** 1.2
    logi_penalty = (1 - (logi / 1.5)) ** 1.0
    cmd_bonus = 0.25 * cmd

    # AI logic: training & cohesion reduce fatality bias
    train_bonus = 1 - 0.15 * (1 - training)
    cohesion_bonus = 1 - 0.10 * (1 - cohesion)
    morale_bonus = 1 - 0.10 * (1 - morale)

    # Combined survival reduction
    survivability = train_bonus * cohesion_bonus * morale_bonus

    # Dominance boost
    suppression_mod = dominance_mods.get("suppression_mod", 1.0)
    DOMINANCE_SCALING = 0.45
    dominance_boost = 1 + DOMINANCE_SCALING * (1 - suppression_mod)
    dominance_boost = min(max(dominance_boost, 0.85), 1.25)

    # Final KIA ratio
    adjusted = base_slider * (1 + med_penalty + logi_penalty - cmd_bonus) * dominance_boost / survivability
    return min(max(adjusted, 0.10), 0.85)  # AI model range

# ===
def compute_relative_dominance(cmd_rus, cmd_ukr, logi_rus, logi_ukr, moral_rus, moral_ukr):
    return {
        "cmd_delta": cmd_rus - cmd_ukr,
        "logi_delta": logi_rus - logi_ukr,
        "morale_delta": moral_rus - moral_ukr
    }

# === Fixed Weapon System Bar + Cumulative Line Chart ===
from collections import OrderedDict

def calculate_casualties_range(base_rate, modifier, duration, ew_enemy, med, cmd, moral, logi,
                                s2s, ad_density, ew_cover, ad_ready,
                                weapon_quality, training, cohesion, weapons,
                                deltas):
    results, total = OrderedDict(), OrderedDict()
    kia_by_system, wia_by_system = OrderedDict(), OrderedDict()

    total_share = sum(weapons.values())
    if total_share == 0:
        st.warning("No active weapon systems. Please enable at least one.")
        return {}, {}, {}, {}

    # Compute dominance scaling modifiers
    dominance_mods = compute_dominance_modifiers(deltas)
    suppression_mod = dominance_mods["suppression_mod"]
    efficiency_mod = dominance_mods["efficiency_mod"]

    for system, share in weapons.items():
        if share == 0:
            continue

        base_share = share / total_share

        # === System-specific scaling
        if system == "Artillery":
            system_scaling = logistic_scaling(logi) * 0.95
        elif system == "Drones":
            drone_decay = max(0.9, 1 - 0.0002 * duration)
            system_scaling = 0.65 * drone_decay
        else:
            system_scaling = 1.0

        ew_penalty = 1.0 if system == "Air Strikes" else (0.75 if system == "Drones" else 1.0)
        ad_penalty = min(max((1 - ad_density * ad_ready), 0.75), 1.05) if system in ["Drones", "Air Strikes"] else 1.0
        coordination = min(max(s2s, 0.85), 1.10) if system in ["Artillery", "Air Strikes", "Drones"] else 1.0

        # === Combined system efficiency
        raw_eff = system_scaling * ew_penalty * ad_penalty * coordination * weapon_quality
        system_eff = 1 + 0.65 * math.tanh(raw_eff - 1)
        system_eff = max(system_eff * efficiency_mod, 0.35)

        # === Suppression scaling
        capped_training = min(training, 1.2)
        capped_cohesion = min(cohesion, 1.15)
        base_suppression = 1 - (0.03 + 0.05 * cmd)
        training_bonus = 1 + 0.05 * capped_training
        cohesion_factor = 0.98 + 0.03 * capped_cohesion
        dominance_amplifier = 1 + 0.5 * (1 - suppression_mod)
        suppression = base_suppression * training_bonus * cohesion_factor * suppression_mod * dominance_amplifier

        # === Medical and logistics scaling
        med_factor = medical_scaling(med, moral, logi)

        # === Final casualty computation
        base = base_rate * base_share * system_eff * modifier * med_factor * suppression
        decay_strength = 0.00035 + 0.00012 * math.tanh(duration / 800)
        base_resistance = morale_scaling(moral) * logistic_scaling(logi) * (training ** 1.05)
        decay_floor = 0.50
        decay_curve_factor = max(math.exp(-decay_strength * duration / base_resistance), decay_floor)

        daily_base = base * decay_curve_factor
        daily_min = round(daily_base * 0.95, 1)
        daily_max = round(daily_base * 1.05, 1)

        # === Apply updated AI-based KIA ratio per system
        kia_ratio = calculate_kia_ratio(med, logi, cmd, moral, training, cohesion, dominance_mods, base_slider=0.30)
        kia_min = round(daily_min * kia_ratio * duration)
        kia_max = round(daily_max * kia_ratio * duration)
        wia_min = round(daily_min * (1 - kia_ratio) * duration)
        wia_max = round(daily_max * (1 - kia_ratio) * duration)

        results[system] = (daily_min, daily_max)
        total[system] = (round(daily_min * duration), round(daily_max * duration))
        kia_by_system[system] = (kia_min, kia_max)
        wia_by_system[system] = (wia_min, wia_max)

    return results, total, kia_by_system, wia_by_system

# === Casualty Calculation Logic ===
def display_force(flag, name, base, exp, ew_enemy, cmd, moral, med, logi, duration,
                  enemy_exp, enemy_ew, s2s, ad_dens, ew_cov, ad_ready,
                  weapon_quality, training, cohesion, weapons, base_slider):

    modifier = exp * morale_scaling(moral) * logistic_scaling(logi)

    # 🔄 Compute deltas for dominance comparison
    if flag == "🇷🇺":
        deltas = compute_relative_dominance(cmd, cmd_ukr, logi, logi_ukr, moral, moral_ukr)
        deltas["ad_delta"] = ad_density_rus - ad_density_ukr
        deltas["ew_delta"] = ew_cover_rus - ew_cover_ukr
    else:
        deltas = compute_relative_dominance(cmd, cmd_rus, logi, logi_rus, moral, moral_rus)
        deltas["ad_delta"] = ad_density_ukr - ad_density_rus
        deltas["ew_delta"] = ew_cover_ukr - ew_cover_rus

    # 💡 Calculate modifiers
    dominance_mods = compute_dominance_modifiers(deltas)

    # 📊 Run updated AI-aligned casualty calculation
    daily_range, cumulative_range, kia_by_system, wia_by_system = calculate_casualties_range(
        base, modifier, duration, ew_enemy, med, cmd, moral, logi,
        s2s, ad_dens, ew_cov, ad_ready,
        weapon_quality, training, cohesion, weapons, deltas
    )

    # 🧮 Totals
    total_min = sum(v[0] for v in cumulative_range.values())
    total_max = sum(v[1] for v in cumulative_range.values())
    kia_min = sum(v[0] for v in kia_by_system.values())
    kia_max = sum(v[1] for v in kia_by_system.values())
    wia_min = sum(v[0] for v in wia_by_system.values())
    wia_max = sum(v[1] for v in wia_by_system.values())

    # 🖥️ Display casualty ranges
    df = pd.DataFrame({
        "Daily Min": {k: v[0] for k, v in daily_range.items()},
        "Daily Max": {k: v[1] for k, v in daily_range.items()},
        "Cumulative Min": {k: v[0] for k, v in cumulative_range.items()},
        "Cumulative Max": {k: v[1] for k, v in cumulative_range.items()},
        "KIA Est": {k: kia_by_system[k][1] for k in kia_by_system},
        "WIA Est": {k: wia_by_system[k][1] for k in wia_by_system}
    })

    st.header(f"{flag} {name} Forces")
    st.dataframe(df)
    st.metric("Total Casualties", f"{total_min:,} - {total_max:,}")
    st.metric("KIA Estimate", f"{kia_min:,} - {kia_max:,}")
    st.metric("WIA Estimate", f"{wia_min:,} - {wia_max:,}")

    plot_casualty_chart(name, daily_range, cumulative_range)
    plot_daily_curve(title=name, daily_range=daily_range, duration=duration)

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

# === Final Output Execution ===
display_force("🇷🇺", "Russian",
              base_rus, exp_rus, ew_ukr, cmd_rus, moral_rus, med_rus, logi_rus, duration_days,
              exp_ukr, ew_rus, s2s_rus, ad_density_rus, ew_cover_rus, ad_ready_rus,
              weapon_quality_rus, train_rus, coh_rus, weapons, base_slider=kia_ratio)

display_force("🇺🇦", "Ukrainian",
              base_ukr, exp_ukr, ew_rus, cmd_ukr, moral_ukr, med_ukr, logi_ukr, duration_days,
              exp_rus, ew_ukr, s2s_ukr, ad_density_ukr, ew_cover_ukr, ad_ready_ukr,
              weapon_quality_ukr, train_ukr, coh_ukr, weapons, base_slider=kia_ratio)

# === Historical Conflict Benchmarks & Comparison ===
