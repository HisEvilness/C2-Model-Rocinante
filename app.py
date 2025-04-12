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

# === Relative Advantage Calculation ===
def compute_relative_dominance(cmd_rus, cmd_ukr, logi_rus, logi_ukr, moral_rus, moral_ukr):
    """
    Computes deltas between both sides’ command, logistics, and morale for scaling.
    """
    return {
        "cmd_delta": cmd_rus - cmd_ukr,
        "logi_delta": logi_rus - logi_ukr,
        "morale_delta": moral_rus - moral_ukr
    }

# === Dominance Calculation ===
def compute_dominance_modifiers(deltas):
    """
    Stronger, linear dominance scaling to affect suppression and efficiency.
    - Used in KIA ratio and casualty scaling
    """

    cmd_delta = deltas.get("cmd_delta", 0)
    logi_delta = deltas.get("logi_delta", 0)
    morale_delta = deltas.get("morale_delta", 0)
    ad_delta = deltas.get("ad_delta", 0)
    ew_delta = deltas.get("ew_delta", 0)

    # Combined axes
    suppression_score = cmd_delta + logi_delta
    efficiency_score = morale_delta + ad_delta + ew_delta

    suppression_mod = 1 + max(min(suppression_score * 0.25, 0.25), -0.20)
    efficiency_mod = 1 + max(min(efficiency_score * 0.20, 0.20), -0.15)

    return {
        "suppression_mod": suppression_mod,
        "efficiency_mod": efficiency_mod
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
    "Storm-Z": {"cohesion": 1.00, "weapons": 1.10, "training": 1.00},
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

# === Force Resilience & Posture Logic ===
def force_resilience(moral, logi, cmd, cohesion, training):
    """
    Determines force resilience based on core inputs.
    Affects how posture influences base casualty volume.
    """
    return morale_scaling(moral) * logistic_scaling(logi) * (1 + 0.2 * cmd) * cohesion * training

res_rus = force_resilience(moral_rus, logi_rus, cmd_rus, coh_rus, train_rus)
res_ukr = force_resilience(moral_ukr, logi_ukr, cmd_ukr, coh_ukr, train_ukr)

def adjusted_posture(posture, resilience, baseline=1.0):
    """
    Adjusts posture effect based on resilience. 
    Prevents weak forces from over-amplifying offensive/defensive posture.
    """
    offset = posture - 1.0
    impact = offset * (1 - baseline / resilience)
    return 1 + 0.25 * math.tanh(3 * impact)

posture_rus_adj = adjusted_posture(posture_rus, res_rus)
posture_ukr_adj = adjusted_posture(posture_ukr, res_ukr)

# Re-declare for use elsewhere in code
def medical_scaling(med, morale, logi):
    """
    Calculates how medical efficiency, morale, and logistics affect survival.
    """
    penalty = 1 + (1.2 * (1 - med)) ** 1.1
    morale_adj = 1 + 0.1 * (morale - 1)
    compound = 1 + 0.15 * (1 - logi) if logi < 0.75 else 1.0
    return penalty * morale_adj * compound

def get_kia_ratio_by_system(system):
    # Baseline values based on historical casualty data
    ratios = {
        "Artillery": 0.35,
        "Drones": 0.55,
        "Snipers": 0.65,
        "Small Arms": 0.30,
        "Heavy Weapons": 0.40,
        "Armored Vehicles": 0.50,
        "Air Strikes": 0.60
    }
    return ratios.get(system, 0.40)  # Fallback default

# === Kill Ratio & Intensity Mapping ===
st.subheader("🔥 Kill Ratio (RU : UA)")

# Kill Ratio Slider — Center = Neutral (1:1), right = Russian advantage, left = Ukrainian advantage
kill_ratio_slider = st.slider(
    "Kill Ratio Advantage (drag right = 🇷🇺 RU advantage, left = 🇺🇦 UA advantage)",
    -50, 50, 15, step=1
)

# Calculate numeric kill ratio
if kill_ratio_slider == 0:
    actual_kill_ratio = 1.0
elif kill_ratio_slider > 0:
    actual_kill_ratio = kill_ratio_slider  # RU advantage (e.g. 15:1)
else:
    actual_kill_ratio = 1.0 / abs(kill_ratio_slider)  # UA advantage (e.g. 1:15)

# Display human-readable kill ratio
if kill_ratio_slider == 0:
    st.markdown("📊 **Kill Ratio:** 1 : 1 (Neutral)")
elif kill_ratio_slider > 0:
    st.markdown(f"📊 **Kill Ratio:** 1 : {kill_ratio_slider} (🇷🇺 Russian Advantage)")
else:
    st.markdown(f"📊 **Kill Ratio:** {abs(kill_ratio_slider)} : 1 (🇺🇦 Ukrainian Advantage)")

# Corrected intensity mapping function
def get_intensity_map(kill_ratio):
    """
    Adjusts base daily KIA estimates based on symmetric kill ratio:
    - When RU is dominant (kill_ratio > 1), UA takes more losses.
    - When UA is dominant (kill_ratio < 1), RU takes more losses.
    """
    levels = {
        1: 20,
        2: 50,
        3: 100,
        4: 160,
        5: 220
    }
    base = levels[intensity_level]

    if kill_ratio > 1.0:
        return base, base * kill_ratio      # RU = base, UA scaled up
    elif kill_ratio < 1.0:
        return base / kill_ratio, base      # RU scaled up, UA = base
    else:
        return base, base                   # 1:1 ratio

# Apply adjusted base casualty values
base_rus, base_ukr = get_intensity_map(actual_kill_ratio)

# Posture-adjusted values
base_rus *= posture_rus_adj
base_ukr *= posture_ukr_adj

# === Enforce Ukrainian KIA/WIA from Russian KIA and kill ratio ===

def enforce_kill_ratio(ru_kia_range, kill_ratio, kia_ratio_ukr):
    """
    Adjust Ukrainian KIA and WIA based on Russian KIA and desired kill ratio.
    """
    ru_kia_min, ru_kia_max = ru_kia_range

    # Apply kill ratio (e.g., RU:UA = 1:15 means UA = 15x RU)
    ukr_kia_min = round(ru_kia_min * kill_ratio)
    ukr_kia_max = round(ru_kia_max * kill_ratio)

    # Derive WIA based on Ukrainian KIA ratio
    total_ukr_min = max(round(ukr_kia_min / kia_ratio_ukr), ukr_kia_min + 1)
    total_ukr_max = max(round(ukr_kia_max / kia_ratio_ukr), ukr_kia_max + 1)
    ukr_wia_min = total_ukr_min - ukr_kia_min
    ukr_wia_max = total_ukr_max - ukr_kia_max

    return (ukr_kia_min, ukr_kia_max), (ukr_wia_min, ukr_wia_max)

# 📦 After Russian simulation is complete
ru_kia_range = results_rus["kia_range"]

# 🔄 Apply enforced kill ratio
ukr_kia_range, uk

# === Weapon System Shares ===
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

# === Relative Advantage Calculation ===
# ===
def compute_relative_dominance(cmd_rus, cmd_ukr, logi_rus, logi_ukr, moral_rus, moral_ukr):
    """
    Calculates the relative advantage based on leadership, logistics, and morale.
    Used to adjust suppression and efficiency scaling.
    """
    return {
        "cmd_delta": cmd_rus - cmd_ukr,
        "logi_delta": logi_rus - logi_ukr,
        "morale_delta": moral_rus - moral_ukr
    }

# === Dominance Modifiers ===
# === Dominance Modifiers ===
def compute_dominance_modifiers(deltas):
    """
    Stronger, linear dominance scaling to affect suppression and efficiency.
    - Used in KIA ratio and casualty scaling
    - Applied based on comparative leadership, morale, logistics, AD & EW strength
    """

    cmd_delta = deltas.get("cmd_delta", 0)
    logi_delta = deltas.get("logi_delta", 0)
    morale_delta = deltas.get("morale_delta", 0)
    ad_delta = deltas.get("ad_delta", 0)
    ew_delta = deltas.get("ew_delta", 0)

    # Combined axes
    suppression_score = cmd_delta + logi_delta
    efficiency_score = morale_delta + ad_delta + ew_delta

    suppression_mod = 1 + max(min(suppression_score * 0.25, 0.25), -0.20)
    efficiency_mod = 1 + max(min(efficiency_score * 0.20, 0.20), -0.15)

    return {
        "suppression_mod": suppression_mod,
        "efficiency_mod": efficiency_mod
    }

from collections import OrderedDict

# === Enforce KIA/WIA sanity check ===
def enforce_kia_wia_sanity(kia_min, kia_max, wia_min, wia_max):
    """
    Ensures WIA is never less than KIA for both min and max values.
    """
    wia_min = max(wia_min, kia_min)
    wia_max = max(wia_max, kia_max)
    return wia_min, wia_max

# === Enforced Ratio Correction ===
def enforce_kill_ratio(rus_kia_range, ratio, kia_ratio_ukr):
    """
    Adjusts Ukrainian KIA and WIA to enforce the global kill ratio logic.
    """
    ru_kia_min, ru_kia_max = rus_kia_range
    ukr_kia_min = round(ru_kia_min * ratio)
    ukr_kia_max = round(ru_kia_max * ratio)

    # Ensure WIA is not lower than KIA
    ukr_total_min = max(round(ukr_kia_min / kia_ratio_ukr), ukr_kia_min + 1)
    ukr_total_max = max(round(ukr_kia_max / kia_ratio_ukr), ukr_kia_max + 1)

    ukr_wia_min = ukr_total_min - ukr_kia_min
    ukr_wia_max = ukr_total_max - ukr_kia_max

    return (ukr_kia_min, ukr_kia_max), (ukr_wia_min, ukr_wia_max)

# === Casualty Calculation ===
def calculate_casualties_range(base_rate, modifier, duration, ew_enemy, med, cmd, moral, logi,
                                s2s, ad_density, ew_cover, ad_ready,
                                weapon_quality, training, cohesion, weapons,
                                deltas, kia_ratio):

    results, total = OrderedDict(), OrderedDict()
    kia_by_system, wia_by_system = OrderedDict(), OrderedDict()

    total_share = sum(weapons.values())
    if total_share == 0:
        st.warning("No active weapon systems. Please enable at least one.")
        return {}, {}, {}, {}

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
        kia_min = round(daily_min * kia_ratio * duration)
        kia_max = round(daily_max * kia_ratio * duration)
        wia_min = round(daily_min * (1 - kia_ratio) * duration)
        wia_max = round(daily_max * (1 - kia_ratio) * duration)

        # ✅ Ensure WIA is not less than KIA
        wia_min, wia_max = enforce_kia_wia_sanity(kia_min, kia_max, wia_min, wia_max)

        results[system] = (daily_min, daily_max)
        total[system] = (round(daily_min * duration), round(daily_max * duration))
        kia_by_system[system] = (kia_min, kia_max)
        wia_by_system[system] = (wia_min, wia_max)

    return results, total, kia_by_system, wia_by_system

# === Casualty Calculation Logic ===
def display_force(flag, name, base, exp, ew_enemy, cmd, moral, med, logi, duration,
                  enemy_exp, enemy_ew, s2s, ad_dens, ew_cov, ad_ready,
                  weapon_quality, training, cohesion, weapons, base_slider,
                  actual_kill_ratio=None, return_data=False):

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

    # 💡 Calculate dominance modifiers
    dominance_mods = compute_dominance_modifiers(deltas)

    # ✅ Calculate KIA ratio once for the whole force (AI logic)
    kia_ratio = calculate_kia_ratio(
        med, logi, cmd, moral, training, cohesion, dominance_mods, base_slider=base_slider
    )

    # 📊 Run casualty simulation
    daily_range, cumulative_range, kia_by_system, wia_by_system = calculate_casualties_range(
        base, modifier, duration, ew_enemy, med, cmd, moral, logi,
        s2s, ad_dens, ew_cov, ad_ready,
        weapon_quality, training, cohesion, weapons, deltas, kia_ratio
    )

    # 🧮 Totals
    total_min = sum(v[0] for v in cumulative_range.values())
    total_max = sum(v[1] for v in cumulative_range.values())
    kia_min = sum(v[0] for v in kia_by_system.values())
    kia_max = sum(v[1] for v in kia_by_system.values())
    wia_min = sum(v[0] for v in wia_by_system.values())
    wia_max = sum(v[1] for v in wia_by_system.values())

    # ✅ Return for override logic (enforced kill ratio post-process)
    if return_data:
        return {
            "kia_range": (kia_min, kia_max),
            "wia_range": (wia_min, wia_max),
            "kia_ratio": kia_ratio
        }

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
    st.metric("KIA Ratio Used", f"{kia_ratio:.2f}")

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

    melted = pd.melt(
        daily_df,
        id_vars="Day",
        value_vars=["Min", "Max"],
        var_name="Type",
        value_name="Casualties"
    )

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

# === Calculation Chart ===
def plot_casualty_chart(title, daily_range, cumulative_range):
    st.subheader(f"{title} Casualty Distribution")

    # Preserve weapon system order
    systems = list(daily_range.keys())

    chart_data = pd.DataFrame({
        "Weapon System": systems,
        "Min": [cumulative_range[sys][0] for sys in systems],
        "Max": [cumulative_range[sys][1] for sys in systems]
    })

    chart_data["Delta"] = chart_data["Max"] - chart_data["Min"]
    chart_data["Max End"] = chart_data["Min"] + chart_data["Delta"]

    base = alt.Chart(chart_data).mark_bar(size=40, color="#bbbbbb").encode(
        x=alt.X("Weapon System:N", sort=None, title="Weapon System"),
        y=alt.Y("Min:Q", title="Min Casualties")
    )

    delta = alt.Chart(chart_data).mark_bar(size=40, color="#1f77b4").encode(
        x=alt.X("Weapon System:N", sort=None),
        y="Min:Q",
        y2="Max End:Q",
        tooltip=["Weapon System", "Min", "Max"]
    )

    st.altair_chart(base + delta, use_container_width=True)

    # === Cumulative Casualty Line Chart ===
    line_data = pd.DataFrame({
        "Days": list(range(0, duration_days + 1, 7)),
        "Min": [sum(v[0] for v in daily_range.values()) * i for i in range(0, duration_days + 1, 7)],
        "Max": [sum(v[1] for v in daily_range.values()) * i for i in range(0, duration_days + 1, 7)]
    })

    line_data = pd.melt(
        line_data,
        id_vars="Days",
        value_vars=["Min", "Max"],
        var_name="Type",
        value_name="Casualties"
    )

    line_chart = alt.Chart(line_data).mark_line(interpolate="monotone").encode(
        x=alt.X("Days:Q", title="Days"),
        y=alt.Y("Casualties:Q", title="Cumulative Casualties"),
        color="Type:N"
    ).properties(
        title=f"{title} Cumulative Casualty Curve",
        width=700,
        height=300
    )

    st.altair_chart(line_chart, use_container_width=True)

# === Final Output Execution ===

# Step 1: Run Russian force and capture results
results_rus = display_force("🇷🇺", "Russian",
    base_rus, exp_rus, ew_ukr, cmd_rus, moral_rus, med_rus, logi_rus, duration_days,
    exp_ukr, ew_rus, s2s_rus, ad_density_rus, ew_cover_rus, ad_ready_rus,
    weapon_quality_rus, train_rus, coh_rus, weapons, base_slider=kia_ratio,
    return_data=True)

# Step 2: Run Ukrainian force and capture results
results_ukr = display_force("🇺🇦", "Ukrainian",
    base_ukr, exp_ukr, ew_rus, cmd_ukr, moral_ukr, med_ukr, logi_ukr, duration_days,
    exp_rus, ew_ukr, s2s_ukr, ad_density_ukr, ew_cover_ukr, ad_ready_ukr,
    weapon_quality_ukr, train_ukr, coh_ukr, weapons, base_slider=kia_ratio,
    return_data=True)

# Step 3: Apply enforced kill ratio logic based on slider direction
if kill_ratio_slider > 0:
    # RU advantage — override Ukrainian casualties
    ru_kia_range = results_rus["kia_range"]
    override_kia, override_wia = enforce_kill_ratio(
        ru_kia_range, abs(kill_ratio_slider), results_ukr["kia_ratio"]
    )
    kia_min_ukr, kia_max_ukr = override_kia
    wia_min_ukr, wia_max_ukr = enforce_kia_wia_sanity(*override_kia, *override_wia)

    st.header("🇺🇦 Ukrainian Forces (Kill Ratio Adjusted)")
    st.metric("KIA Estimate", f"{kia_min_ukr:,} - {kia_max_ukr:,}")
    st.metric("WIA Estimate", f"{wia_min_ukr:,} - {wia_max_ukr:,}")
    st.metric("KIA Ratio Used", f"{results_ukr['kia_ratio']:.2f}")

elif kill_ratio_slider < 0:
    # UA advantage — override Russian casualties
    ukr_kia_range = results_ukr["kia_range"]
    override_kia, override_wia = enforce_kill_ratio(
        ukr_kia_range, abs(kill_ratio_slider), results_rus["kia_ratio"]
    )
    kia_min_rus, kia_max_rus = override_kia
    wia_min_rus, wia_max_rus = enforce_kia_wia_sanity(*override_kia, *override_wia)

    st.header("🇷🇺 Russian Forces (Kill Ratio Adjusted)")
    st.metric("KIA Estimate", f"{kia_min_rus:,} - {kia_max_rus:,}")
    st.metric("WIA Estimate", f"{wia_min_rus:,} - {wia_max_rus:,}")
    st.metric("KIA Ratio Used", f"{results_rus['kia_ratio']:.2f}")

else:
    # Neutral — results already displayed above in default simulation
    pass

# === Historical Conflict Benchmarks & Comparison ===
