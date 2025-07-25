import math
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ===== Constants =====
METAL_DENSITIES = {
    "Grey Iron": 7100,
    "Steel": 7800,
    "Aluminum": 2700,
    "Copper": 8960,
    "Zinc": 7140
}

FURNACE_EFFICIENCY = {
    "Cupola": {'m_low': 1.05, 'm_high': 1.12, 'eff_low': 3.0, 'eff_high': 3.5},
    "Induction": {'m_low': 1.01, 'm_high': 1.04, 'eff_low': 1.4, 'eff_high': 2.0},
    "Electric Arc": {'m_low': 1.02, 'm_high': 1.07, 'eff_low': 2.0, 'eff_high': 2.5},
    "Oil/Gas": {'m_low': 1.05, 'm_high': 1.10, 'eff_low': 3.25, 'eff_high': 3.5}
}

REJECTION_FACTORS = {
    "Grey Iron": {"High": 1.08, "Medium": 1.035, "Low": 1.01},
    "Steel": {"High": 1.095, "Medium": 1.075, "Low": 1.025}
}

# ===== Calculation Functions =====
def direct_material_cost(p):
    mass = p['density'] * (p['volume_cm3'] / 1e6)
    return mass * p['unit_metal_cost'] * p['f_m'] * p['f_p'] * p['f_f']

def indirect_material_cost(p):
    return (p['mold_sand_weight'] * p['mold_sand_cost'] +
            p['core_sand_weight'] * p['core_sand_cost'] +
            p['misc_material_cost'])

def labor_cost(p):
    return p['labor_hours'] * p['labor_rate'] * p['f_r']

def energy_cost(p):
    mass = p['density'] * (p['volume_cm3'] / 1e6)
    melt = mass * p['energy_cost'] * p['f_eta'] * p['f_y']
    other = mass * p['other_energy_rate']
    return melt + other

def tooling_cost(p):
    V = p['volume_cm3'] / 1e6
    rel = math.exp(0.629 * V + 0.048 * p['accuracy'] + 0.023 * p['shape'] + 0.739)
    return (rel * p['tooling_index']) / p['quantity']

def overhead_cost(p):
    mass = p['density'] * (p['volume_cm3'] / 1e6)
    return mass * (p['admin_rate'] + p['depr_rate'])

def total_costs(p):
    costs = {
        'Direct Material': direct_material_cost(p),
        'Indirect Material': indirect_material_cost(p),
        'Labor': labor_cost(p),
        'Energy': energy_cost(p),
        'Tooling': tooling_cost(p),
        'Overhead': overhead_cost(p)
    }
    costs['Total'] = sum(costs.values())
    return costs

# ===== Main App =====
def main():
    st.set_page_config(layout="wide", page_title="Casting Cost Estimator")
    st.title("Brafe Engineering Casting Cost Estimator")

    # Sidebar Inputs
    with st.sidebar:
        st.header("Input Parameters")
        quote = st.number_input("Quoted Price (£)", value=1000.0)
        metal = st.selectbox("Metal Type", list(METAL_DENSITIES.keys()))
        volume_cm3 = st.number_input("Volume (cm³)", value=1830.0)
        
        if 'prev_metal' not in st.session_state or st.session_state.prev_metal != metal:
            st.session_state.prev_metal = metal
            st.session_state.density = METAL_DENSITIES[metal]
        
        density = st.number_input("Density (kg/m³)", value=st.session_state.density)
        unit_metal_cost = st.number_input("Metal Cost (£/kg)", value=1.0)
        quantity = st.number_input("Order Quantity", value=5000, step=1)
        shape = st.slider("Shape Complexity (0-100)", 0, 100, 30)
        accuracy = st.slider("Accuracy Index (1-100)", 1, 100, 35)

        st.subheader("Process Factors")
        furnace = st.selectbox("Furnace Type", list(FURNACE_EFFICIENCY.keys()))
        fe = FURNACE_EFFICIENCY[furnace]

        col1, col2 = st.columns(2)
        with col1:
            f_m = st.slider("Melting Loss fₘ", fe['m_low'], fe['m_high'], (fe['m_low'] + fe['m_high']) / 2)
            f_p = st.slider("Pouring Loss fₚ", 1.01, 1.07, 1.03)
            f_f = st.slider("Fettling Loss f_f", 1.01, 1.07, 1.05)
        with col2:
            f_y = st.slider("Yield Factor f_y", 0.5, 1.0, 0.76)
            f_eta = st.slider("Furnace Efficiency η", fe['eff_low'], fe['eff_high'], (fe['eff_low'] + fe['eff_high']) / 2)

        quality = st.selectbox("Quality Level", ["High", "Medium", "Low"])
        f_r = REJECTION_FACTORS.get(metal, {}).get(quality, 1.0)
        st.info(f"Rejection Factor: {f_r}")

        st.subheader("Labor")
        labor_hours = st.number_input("Labor Hours", value=2.0)
        labor_rate = st.number_input("Labor Rate (£/h)", value=16.0)

        st.subheader("Materials & Overheads")
        col1, col2 = st.columns(2)
        with col1:
            mold_sand_weight = st.number_input("Mold Sand Weight (kg)", value=5.0)
            mold_sand_cost = st.number_input("Mold Sand Cost (£/kg)", value=0.05)
            core_sand_weight = st.number_input("Core Sand Weight (kg)", value=1.0)
            core_sand_cost = st.number_input("Core Sand Cost (£/kg)", value=0.10)
            misc_material_cost = st.number_input("Misc. Material Cost (£)", value=0.0)
        with col2:
            tooling_index = st.number_input("Tooling Cost Index", value=1000.0)
            admin_rate = st.number_input("Admin Cost (£/kg)", value=3.0)
            depr_rate = st.number_input("Depreciation (£/kg)", value=0.15)
            energy_cost_rate = st.number_input("Energy Cost (£/kWh)", value=0.10)
            other_energy_rate = st.number_input("Other Energy (£/kg)", value=0.50)

    # Collect Parameters
    params = {
        'density': density,
        'volume_cm3': volume_cm3,
        'unit_metal_cost': unit_metal_cost,
        'quantity': quantity,
        'shape': shape,
        'accuracy': accuracy,
        'f_m': f_m,
        'f_p': f_p,
        'f_f': f_f,
        'f_y': f_y,
        'f_eta': f_eta,
        'f_r': f_r,
        'labor_hours': labor_hours,
        'labor_rate': labor_rate,
        'mold_sand_weight': mold_sand_weight,
        'mold_sand_cost': mold_sand_cost,
        'core_sand_weight': core_sand_weight,
        'core_sand_cost': core_sand_cost,
        'misc_material_cost': misc_material_cost,
        'tooling_index': tooling_index,
        'admin_rate': admin_rate,
        'depr_rate': depr_rate,
        'energy_cost': energy_cost_rate,
        'other_energy_rate': other_energy_rate,
        'metal': metal,
        'furnace': furnace,
        'quote': quote
    }

    # Cost Calculation and Display
    if st.button("Calculate Total Cost"):
        costs = total_costs(params)

        st.subheader("Cost Breakdown")
        col1, col2 = st.columns([1, 2])

        with col1:
            df = pd.DataFrame.from_dict(costs, orient='index', columns=['£ Amount'])
            st.dataframe(df.style.format("£{:,.2f}"))

            variance = quote - costs['Total']
            st.metric("Variance (Quote vs Actual)", f"£{variance:,.2f}",
                      delta_color="inverse" if variance < 0 else "normal")

        with col2:
            pie_fig, pie_ax = plt.subplots()
            labels = [k for k in costs.keys() if k != 'Total']
            pie_ax.pie([costs[k] for k in labels], labels=labels, autopct='%1.1f%%')
            pie_ax.set_title("Cost Distribution")
            st.pyplot(pie_fig)

            bar_fig, bar_ax = plt.subplots()
            bar_ax.bar(labels, [costs[k] for k in labels])
            bar_ax.set_ylabel("Cost (£)")
            bar_ax.set_title("Cost by Category")
            bar_ax.tick_params(axis='x', rotation=45)
            st.pyplot(bar_fig)

# ===== Run App =====
if __name__ == "__main__":
    main()
