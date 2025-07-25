import math
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Constants and lookup tables
METAL_DENSITIES = {
    "Grey Iron": 7100,      # kg/m³
    "Steel": 7800,
    "Aluminum": 2700,
    "Copper": 8960,
    "Zinc": 7140
}

FURNACE_EFFICIENCY = {
    "Cupola":    {'m_low':1.05,'m_high':1.12,'eff_low':3.0,'eff_high':3.5},
    "Induction": {'m_low':1.01,'m_high':1.04,'eff_low':1.4,'eff_high':2.0},
    "Electric Arc": {'m_low':1.02,'m_high':1.07,'eff_low':2.0,'eff_high':2.5},
    "Oil/Gas":   {'m_low':1.05,'m_high':1.10,'eff_low':3.25,'eff_high':3.5}
}

REJECTION_FACTORS = {
    "Grey Iron": {"High":1.08, "Medium":1.035, "Low":1.01},
    "Steel":     {"High":1.095,"Medium":1.075, "Low":1.025}
}

# ====== Calculation functions ======
def direct_material_cost(p):
    mass = p['density'] * (p['volume_cm3']/1e6)
    return mass * p['unit_metal_cost'] * p['f_m'] * p['f_p'] * p['f_f']

def indirect_material_cost(p):
    mold = p['mold_sand_weight'] * p['mold_sand_cost']
    core = p['core_sand_weight'] * p['core_sand_cost']
    misc = p['misc_material_cost']
    return mold + core + misc

def labor_cost(p):
    return p['labor_hours'] * p['labor_rate'] * p['f_r']

def energy_cost(p):
    mass = p['density'] * (p['volume_cm3']/1e6)
    melt = mass * p['energy_cost'] * p['f_eta'] * p['f_y']
    other = mass * p['other_energy_rate']
    return melt + other

def tooling_cost(p):
    V = p['volume_cm3']/1e6
    rel = math.exp(0.629*V + 0.048*p['accuracy'] + 0.023*p['shape'] + 0.739)
    return (rel * p['tooling_index'])/p['quantity']

def overhead_cost(p):
    mass = p['density'] * (p['volume_cm3']/1e6)
    return mass * (p['admin_rate'] + p['depr_rate'])

def total_costs(p):
    costs = {}
    costs['Direct Mat'] = direct_material_cost(p)
    costs['Indirect Mat'] = indirect_material_cost(p)
    costs['Labor'] = labor_cost(p)
    costs['Energy'] = energy_cost(p)
    costs['Tooling'] = tooling_cost(p)
    costs['Overhead'] = overhead_cost(p)
    costs['Total'] = sum(costs.values())
    return costs

def pie_chart(costs):
    fig, ax = plt.subplots()
    labels = list(costs.keys())[:-1]
    sizes = [costs[k] for k in labels]
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    ax.set_title('Cost Breakdown')
    return fig

def bar_chart(costs):
    fig, ax = plt.subplots()
    labels = list(costs.keys())[:-1]
    values = [costs[k] for k in labels]
    ax.bar(labels, values)
    ax.set_ylabel('£')
    ax.set_title('Cost Category Values')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    return fig

# ====== Streamlit App ======
st.set_page_config(layout="wide", page_title="Casting Cost Estimator")
st.title("Brafe Engineering Casting Cost Estimator")

# Initialize session state
if 'costs' not in st.session_state:
    st.session_state.costs = None

# Create form
with st.form("cost_form"):
    # Part & Quote
    st.header("Part & Quote")
    quote = st.number_input("Quoted Price (£)", value=1000.0, step=50.0, key='quote')
    labor_hours = st.number_input("Labor Hours", value=2.0, step=0.5, key='labor_hours')
    unit_metal_cost = st.number_input("Material Cost/kg", value=1.5, step=0.1, key='unit_metal_cost')
    labor_rate = st.number_input("Labor Rate (£/hr)", value=25.0, step=1.0, key='labor_rate')
    
    # Geometry & Material
    st.header("Geometry & Material")
    col1, col2 = st.columns(2)
    with col1:
        metal = st.selectbox("Metal", list(METAL_DENSITIES.keys()), key='metal')
        volume_cm3 = st.number_input("Volume (cm³)", value=1830.0, step=50.0, key='volume_cm3')
    with col2:
        density = st.number_input("Density (kg/m³)", value=METAL_DENSITIES[metal], step=100.0, key='density')
        st.button("Sync Density", on_click=lambda: st.session_state.update(density=METAL_DENSITIES[st.session_state.metal]))
    
    # Casting Parameters
    st.header("Casting Parameters")
    shape = st.slider("Shape Complexity", 0, 100, 30, key='shape')
    accuracy = st.slider("Accuracy", 1, 100, 35, key='accuracy')
    quantity = st.number_input("Quantity", value=5000, step=100, key='quantity')
    
    # Process & Costs
    st.header("Process & Costs")
    col1, col2 = st.columns(2)
    with col1:
        furnace = st.selectbox("Furnace Type", list(FURNACE_EFFICIENCY.keys()), key='furnace')
        f_y = st.number_input("Yield (f_y)", value=0.76, step=0.01, key='f_y')
        f_r = st.number_input("Rejection Factor (f_r)", value=1.05, step=0.01, key='f_r')
    with col2:
        f_m = st.number_input("Melting Loss (f_m)", value=1.05, step=0.01, key='f_m')
        f_p = st.number_input("Pouring Loss (f_p)", value=1.03, step=0.01, key='f_p')
        f_f = st.number_input("Fettling Loss (f_f)", value=1.05, step=0.01, key='f_f')
    
    # Sands & Rates
    st.header("Sands & Rates")
    col1, col2 = st.columns(2)
    with col1:
        mold_sand_weight = st.number_input("Mold Sand Weight (kg)", value=5.0, step=0.5, key='mold_sand_weight')
        mold_sand_cost = st.number_input("Mold Sand Cost (£/kg)", value=0.05, step=0.01, key='mold_sand_cost')
    with col2:
        core_sand_weight = st.number_input("Core Sand Weight (kg)", value=1.0, step=0.1, key='core_sand_weight')
        core_sand_cost = st.number_input("Core Sand Cost (£/kg)", value=0.10, step=0.01, key='core_sand_cost')
    misc_material_cost = st.number_input("Misc Material Cost (£)", value=0.0, step=1.0, key='misc_material_cost')
    
    # Overheads & Tooling
    st.header("Overheads & Tooling")
    col1, col2 = st.columns(2)
    with col1:
        tooling_index = st.number_input("Tooling Index", value=1000.0, step=100.0, key='tooling_index')
        admin_rate = st.number_input("Admin Overhead (£/kg)", value=3.0, step=0.1, key='admin_rate')
    with col2:
        depr_rate = st.number_input("Depreciation (£/kg)", value=0.15, step=0.01, key='depr_rate')
        energy_cost_val = st.number_input("Energy Cost (£/kWh)", value=0.10, step=0.01, key='energy_cost')
        other_energy_rate = st.number_input("Other Energy (£/kg)", value=0.50, step=0.1, key='other_energy_rate')
    
    # Submit button
    submitted = st.form_submit_button("Calculate Costs")

# Calculations
if submitted:
    try:
        # Create parameters dictionary
        p = {k: st.session_state[k] for k in [
            'density', 'volume_cm3', 'unit_metal_cost', 'f_m', 'f_p', 'f_f',
            'mold_sand_weight', 'mold_sand_cost', 'core_sand_weight', 'core_sand_cost',
            'misc_material_cost', 'labor_hours', 'labor_rate', 'f_r', 'energy_cost',
            'f_eta', 'f_y', 'other_energy_rate', 'tooling_index', 'quantity',
            'admin_rate', 'depr_rate', 'shape', 'accuracy'
        ]}
        p['metal'] = st.session_state.metal
        p['furnace'] = st.session_state.furnace
        
        # Set furnace efficiency
        fe = FURNACE_EFFICIENCY[p['furnace']]
        p['f_eta'] = (fe['eff_low'] + fe['eff_high']) / 2
        
        # Calculate costs
        costs = total_costs(p)
        st.session_state.costs = costs
        
    except Exception as e:
        st.error(f"Calculation error: {str(e)}")

# Display results
if st.session_state.costs:
    st.header("Results")
    
    # Cost breakdown
    st.subheader("Cost Breakdown")
    result_text = ""
    for k, v in st.session_state.costs.items():
        result_text += f"{k:15}: £{v:,.2f}\n"
    result_text += f"\nQuote Variance: £{quote - st.session_state.costs['Total']:,.2f}"
    st.text_area("Cost Details", value=result_text, height=200)
    
    # Charts
    col1, col2 = st.columns(2)
    with col1:
        st.pyplot(pie_chart(st.session_state.costs))
    with col2:
        st.pyplot(bar_chart(st.session_state.costs))
    
    # Export button
    if st.button("Export CSV"):
        df = pd.DataFrame.from_dict(st.session_state.costs, orient='index', columns=['Cost'])
        csv = df.to_csv()
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="casting_costs.csv",
            mime="text/csv"
        )
