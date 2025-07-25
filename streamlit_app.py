# Streamlit App: Advanced Casting Cost Estimator with Enhanced UI for GitHub
# ==============================================================================

import math
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set global seaborn theme
sns.set_theme(style="whitegrid")

# ----- CONSTANTS -------------------------------------------------------------
METAL_DENSITIES = {
    "Grey Iron": 7100.0,
    "Steel": 7800.0,
    "Aluminum": 2700.0,
    "Copper": 8960.0,
    "Zinc": 7140.0
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

# ----- CALCULATIONS ----------------------------------------------------------
def direct_material_cost(p):
    mass = p['density'] * (p['volume_cm3'] / 1e6)
    return mass * p['unit_metal_cost'] * p['f_m'] * p['f_p']

def indirect_material_cost(p):
    mould = p['mold_sand_weight'] * p['mold_sand_cost'] * p['sand_recycle_factor'] * p['f_r'] * p['mold_rejection_factor']
    core = p['core_sand_weight'] * p['core_sand_cost'] * p['sand_recycle_factor'] * p['f_r'] * p['core_rejection_factor']
    return mould + core + p['misc_material_cost']

def labour_cost(p):
    qual = p['design_rejection'] * p['salary_high_qual'] * p['designers_count'] * p['design_hours'] / p['quantity']
    tech = p['f_r'] * p['activity_rejection'] * p['salary_technical'] * p['technicians_count'] * p['labor_hours'] / p['quantity']
    return qual + tech

def energy_cost(p):
    mass = p['density'] * (p['volume_cm3'] / 1e6)
    melting = p['energy_cost'] * p['melting_energy'] * (mass * 1.3) / 1000
    holding = p['energy_cost'] * p['holding_energy'] * p['holding_time'] * (mass * 1.3) / 1000
    return melting + holding + mass * p['other_energy_rate']

def tooling_cost(p):
    software = p['software_updates_cost'] / p['design_units_produced']
    consumables = p['tooling_consumables_cost'] / p['quantity']
    maintenance = p['equipment_maintenance_cost'] / p['quantity']
    machining = p['machining_cost_per_hour'] * p['machining_time']
    return software + consumables + maintenance + machining

def post_casting_costs(p):
    costs = {
        'Fettling': p['fettling_labor_hours'] * p['fettling_labor_rate'] + p['fettling_equipment_cost'],
        'Heat Treatment': p['heat_treatment_energy'] * p['energy_cost'] + p['heat_treatment_labor_hours'] * p['heat_treatment_labor_rate'],
        'NDT': p['ndt_cost_per_part'],
        'Pressure Testing': p['pressure_testing_labor_hours'] * p['pressure_testing_labor_rate'] + p['pressure_testing_equipment_cost'],
        'Final Inspection': p['inspection_labor_hours'] * p['inspection_labor_rate'],
        'Radiography': p['radiography_cost_per_part'],
        'Plating': p['plating_material_cost'] + p['plating_labor_hours'] * p['plating_labor_rate']
    }
    return costs

def overhead_cost(p, man_cost):
    admin = man_cost * p['admin_percentage'] / 100
    depr = man_cost * p['depr_percentage'] / 100
    return admin + depr

def total_costs(p):
    direct = direct_material_cost(p)
    indirect = indirect_material_cost(p)
    labour = labour_cost(p)
    energy = energy_cost(p)
    tooling = tooling_cost(p)
    post = post_casting_costs(p)
    post_total = sum(post.values())
    man_cost = direct + indirect + labour + energy + tooling + post_total
    overhead = overhead_cost(p, man_cost)
    total = man_cost + overhead

    breakdown = {
        'Direct Material': direct,
        'Indirect Material': indirect,
        'Labour': labour,
        'Energy': energy,
        'Tooling': tooling,
        'Post Casting': post_total,
        'Overheads': overhead,
        'Total': total
    }
    return breakdown, post

# ----- STREAMLIT UI ----------------------------------------------------------
def main():
    st.set_page_config(page_title="Casting Cost Estimator", layout="wide", page_icon="🧱")
    st.title("🧱 Advanced Casting Cost Estimator")
    st.markdown("<style>h1{color:#2c3e50;}</style>", unsafe_allow_html=True)
    st.caption("Enhanced version for GitHub deployment | Research base: Metals 2023, 13(2), 216")

    st.markdown("---")
    st.header("📥 Input Parameters")
    st.info("Use the sidebar to input all required parameters.")

    with st.sidebar:
        st.title("⚙️ Parameters Setup")
        st.markdown("Configure your process parameters below.")

        # Example default setup (this block would normally continue)
        p = {}
        p['quote'] = st.number_input("Quoted Price (£)", value=1000.0)
        p['metal'] = st.selectbox("Metal Type", METAL_DENSITIES.keys())
        p['volume_cm3'] = st.number_input("Volume (cm³)", value=1500.0)
        p['density'] = METAL_DENSITIES[p['metal']]
        p['unit_metal_cost'] = st.number_input("Metal Cost (£/kg)", value=1.0)
        p['quantity'] = st.number_input("Order Quantity", value=500)
        p['f_m'] = 1.05
        p['f_p'] = 1.02
        p['f_r'] = 1.05
        p['mold_sand_weight'] = 5
        p['mold_sand_cost'] = 0.05
        p['core_sand_weight'] = 1
        p['core_sand_cost'] = 0.1
        p['sand_recycle_factor'] = 0.7
        p['misc_material_cost'] = 10
        p['mold_rejection_factor'] = 1.05
        p['core_rejection_factor'] = 1.05
        p['designers_count'] = 2
        p['design_hours'] = 40
        p['salary_high_qual'] = 60
        p['design_rejection'] = 1.1
        p['technicians_count'] = 3
        p['labor_hours'] = 8
        p['salary_technical'] = 25
        p['activity_rejection'] = 1.05
        p['energy_cost'] = 0.1
        p['melting_energy'] = 580
        p['holding_energy'] = 0.4
        p['holding_time'] = 30
        p['other_energy_rate'] = 0.5
        p['software_updates_cost'] = 5000
        p['design_units_produced'] = 50
        p['tooling_consumables_cost'] = 200
        p['equipment_maintenance_cost'] = 1000
        p['machining_cost_per_hour'] = 40
        p['machining_time'] = 2
        p['admin_percentage'] = 10
        p['depr_percentage'] = 20
        p['fettling_labor_hours'] = 0.5
        p['fettling_labor_rate'] = 25
        p['fettling_equipment_cost'] = 5
        p['heat_treatment_energy'] = 50
        p['heat_treatment_labor_rate'] = 30
        p['heat_treatment_labor_hours'] = 1
        p['ndt_cost_per_part'] = 15
        p['inspection_labor_hours'] = 0.5
        p['inspection_labor_rate'] = 25
        p['pressure_testing_labor_hours'] = 0.5
        p['pressure_testing_labor_rate'] = 35
        p['pressure_testing_equipment_cost'] = 20
        p['radiography_cost_per_part'] = 25
        p['plating_material_cost'] = 15
        p['plating_labor_hours'] = 1
        p['plating_labor_rate'] = 30

    st.markdown("---")

    if st.button("🚀 Run Cost Estimation"):
        st.success("Calculation Complete!")
        breakdown, post = total_costs(p)

        df_main = pd.DataFrame(breakdown.items(), columns=["Category", "Cost (£)"])
        df_post = pd.DataFrame(post.items(), columns=["Post-Process", "Cost (£)"])

        st.subheader("📊 Summary Breakdown")
        st.dataframe(df_main.style.format("£{:,.2f}"))

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Pie Chart")
            fig1, ax1 = plt.subplots()
            ax1.pie(df_main["Cost (£)"][:-1], labels=df_main["Category"][:-1], autopct='%1.1f%%', startangle=90)
            st.pyplot(fig1)

        with col2:
            st.subheader("Bar Chart")
            fig2, ax2 = plt.subplots()
            sns.barplot(data=df_main[:-1], x="Category", y="Cost (£)", ax=ax2)
            ax2.tick_params(axis='x', rotation=45)
            st.pyplot(fig2)

        with st.expander("🔍 Post-Casting Process Breakdown"):
            st.dataframe(df_post.style.format("£{:,.2f}"))
            fig3, ax3 = plt.subplots()
            sns.barplot(data=df_post, x="Post-Process", y="Cost (£)", ax=ax3)
            ax3.tick_params(axis='x', rotation=45)
            st.pyplot(fig3)

        st.download_button(
            "📥 Download Cost Report CSV",
            df_main.to_csv(index=False).encode(),
            f"cost_estimation_{p['metal']}_{p['quantity']}pcs.csv",
            "text/csv"
        )

if __name__ == "__main__":
    main()
