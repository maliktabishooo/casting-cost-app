import math
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ===== CONSTANTS ==============================================================
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

# ===== CALCULATION FUNCTIONS ==================================================
def direct_material_cost(params):
    """Calculate direct material cost (Eq.3)"""
    mass = params['density'] * (params['volume_cm3'] / 1e6)  # kg
    return mass * params['unit_metal_cost'] * params['f_m'] * params['f_p']

def indirect_material_cost(params):
    """Calculate indirect material cost (Eq.4-9)"""
    mould_sand = (params['mold_sand_weight'] * params['mold_sand_cost']
                  * params['sand_recycle_factor'] * params['f_r']
                  * params['mold_rejection_factor'])
    core_sand = (params['core_sand_weight'] * params['core_sand_cost']
                 * params['sand_recycle_factor'] * params['f_r']
                 * params['core_rejection_factor'])
    return mould_sand + core_sand + params['misc_material_cost']

def labour_cost(params):
    """Calculate labor cost (Eq.11-13)"""
    highly_qualified = (params['design_rejection']
                        * params['salary_high_qual']
                        * params['designers_count']
                        * params['design_hours']
                        / params['quantity'])
    technical = (params['f_r'] * params['activity_rejection']
                 * params['salary_technical']
                 * params['technicians_count']
                 * params['labor_hours']
                 / params['quantity'])
    return highly_qualified + technical

def energy_cost(params):
    """Calculate energy cost (Eq.14-20)"""
    mass = params['density'] * (params['volume_cm3'] / 1e6)  # kg
    melting = (params['energy_cost'] * params['melting_energy']
               * (mass * 1.3) / 1000)  # 30% extra for feeder/gating
    holding = (params['energy_cost'] * params['holding_energy']
               * params['holding_time'] * (mass * 1.3) / 1000)
    return melting + holding + mass * params['other_energy_rate']

def tooling_cost(params):
    """Calculate tooling cost (Eq.21-22)"""
    software = params['software_updates_cost'] / params['design_units_produced']
    consumables = params['tooling_consumables_cost'] / params['quantity']
    maintenance = params['equipment_maintenance_cost'] / params['quantity']
    machining = params['machining_cost_per_hour'] * params['machining_time']
    return software + consumables + maintenance + machining

def post_casting_costs(params):
    """Calculate all post-casting processing costs"""
    costs = {}
    costs['Fettling'] = (params['fettling_labor_hours'] * params['fettling_labor_rate']
                         + params['fettling_equipment_cost'])
    heat_treatment = (params['heat_treatment_energy'] * params['energy_cost']
                      + params['heat_treatment_labor_hours'] * params['heat_treatment_labor_rate'])
    costs['Heat Treatment'] = heat_treatment
    costs['NDT'] = params['ndt_cost_per_part']
    costs['Pressure Testing'] = (params['pressure_testing_labor_hours'] * params['pressure_testing_labor_rate']
                                 + params['pressure_testing_equipment_cost'])
    costs['Final Inspection'] = params['inspection_labor_hours'] * params['inspection_labor_rate']
    costs['Radiography'] = params['radiography_cost_per_part']
    costs['Plating'] = params['plating_cost']
    return costs

def overhead_cost(params, manufacturing_cost):
    """Calculate overhead cost (Eq.23)"""
    admin = manufacturing_cost * params['admin_percentage'] / 100
    depreciation = manufacturing_cost * params['depr_percentage'] / 100
    return admin + depreciation

def total_costs(params):
    """Calculate total cost (Eq.1)"""
    direct_mat = direct_material_cost(params)
    indirect_mat = indirect_material_cost(params)
    material_cost = direct_mat + indirect_mat
    labour = labour_cost(params)
    energy = energy_cost(params)
    tooling_val = tooling_cost(params)
    post_casting = post_casting_costs(params)
    post_casting_total = sum(post_casting.values())
    manufacturing_cost = material_cost + labour + energy + tooling_val + post_casting_total
    overheads = overhead_cost(params, manufacturing_cost)
    total_cost = manufacturing_cost + overheads
    profit_loss = params['quote'] - total_cost
    profit_loss_percent = (profit_loss / params['quote'] * 100) if params['quote'] else 0
    cost_breakdown = {
        'Direct Material': direct_mat,
        'Indirect Material': indirect_mat,
        'Labour': labour,
        'Energy': energy,
        'Tooling': tooling_val,
        'Post Casting': post_casting_total,
        'Overheads': overheads,
        'Total': total_cost,
        'Profit/Loss': profit_loss
    }
    return cost_breakdown, post_casting, profit_loss, profit_loss_percent

# ===== STREAMLIT UI ===========================================================
def main():
    # Construct the absolute path to the image file
    script_dir = Path(__file__).parent
    image_path = script_dir / "budget.png"
    st.set_page_config(
        layout="wide",
        page_title="Advanced Casting Cost Estimator",
        page_icon=str(image_path)
    )

    # Custom CSS for enhanced color scheme and professional styling
    st.markdown("""
        <style>
        .main {
            background: linear-gradient(to bottom right, #f8f9fa, #e9ecef);
            padding: 20px;
            border-radius: 10px;
        }
        .stButton>button {
            background-color: #007bff;
            color: white;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: bold;
            transition: background-color 0.3s;
        }
        .stButton>button:hover {
            background-color: #0056b3;
        }
        .stMetric {
            background-color: #ffffff;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stSidebar {
            background-color: #f1f3f5;
            padding: 20px;
            border-radius: 10px;
        }
        h1, h2, h3 {
            color: #343a40;
            font-family: 'Arial', sans-serif;
        }
        .stSelectbox, .stNumberInput, .stSlider {
            background-color: #ffffff;
            border-radius: 5px;
            padding: 5px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Create columns for the title and image
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image(str(image_path), width=120)
    with col2:
        st.title("Advanced Casting Cost Estimator")
        st.caption("Based on research: Metals 2023, 13(2), 216 - Cost Estimation of Metal Casting with Sand Mould")

    # Initialize session state
    if 'density' not in st.session_state:
        st.session_state.density = METAL_DENSITIES["Grey Iron"]
    if 'prev_metal' not in st.session_state:
        st.session_state.prev_metal = "Grey Iron"

    # Sidebar for inputs
    with st.sidebar:
        st.header("⚙️ Basic Parameters")
        params = {}
        params['quote'] = st.number_input("Quoted Price (£)", value=1000.0, min_value=0.0)
        params['metal'] = st.selectbox("Metal Type", list(METAL_DENSITIES.keys()))
        params['volume_cm3'] = st.number_input("Volume (cm³)", value=1830.0, min_value=0.0)
        if st.session_state.prev_metal != params['metal']:
            st.session_state.density = METAL_DENSITIES[params['metal']]
            st.session_state.prev_metal = params['metal']
        params['density'] = st.number_input(
            "Density (kg/m³)",
            value=float(st.session_state.density),
            min_value=0.0,
            step=1.0
        )
        st.session_state.density = params['density']
        params['unit_metal_cost'] = st.number_input("Metal Cost (£/kg)", value=1.0, min_value=0.0)
        params['quantity'] = st.number_input("Order Quantity", value=5000, min_value=1)
        params['shape'] = st.slider("Shape Complexity (0-100)", 0, 100, 30)
        params['accuracy'] = st.slider("Accuracy Index (1-100)", 1, 100, 35)

        st.subheader("🔥 Process Factors")
        params['furnace'] = st.selectbox("Furnace Type", list(FURNACE_EFFICIENCY.keys()))
        fe = FURNACE_EFFICIENCY[params['furnace']]
        col1, col2 = st.columns(2)
        with col1:
            params['f_m'] = st.slider("Melting Loss (fₘ)",
                                      float(fe['m_low']),
                                      float(fe['m_high']),
                                      float((fe['m_low'] + fe['m_high'])/2))
            params['f_p'] = st.slider("Pouring Loss (fₚ)", 1.01, 1.07, 1.03)
        with col2:
            params['f_y'] = st.slider("Yield Factor (f_y)", 0.5, 1.0, 0.76)
            params['f_eta'] = st.slider("Furnace Eff. (η)",
                                        float(fe['eff_low']),
                                        float(fe['eff_high']),
                                        float((fe['eff_low'] + fe['eff_high'])/2))
        quality = st.selectbox("Quality Level", ["High", "Medium", "Low"])
        params['f_r'] = REJECTION_FACTORS.get(params['metal'], {}).get(quality, 1.0)
        st.info(f"Rejection Factor: {params['f_r']:.3f}")

        st.subheader("👷 Labor Parameters")
        col1, col2 = st.columns(2)
        with col1:
            params['designers_count'] = st.number_input("Design Engineers", value=2, min_value=1)
            params['design_hours'] = st.number_input("Design Hours", value=40.0, min_value=0.0)
            params['salary_high_qual'] = st.number_input("High-Qual Salary (£/h)", value=60.0, min_value=0.0)
            params['design_rejection'] = st.slider("Design Rejection Factor", 1.0, 1.2, 1.1)
        with col2:
            params['technicians_count'] = st.number_input("Technicians", value=3, min_value=1)
            params['labor_hours'] = st.number_input("Labor Hours", value=8.0, min_value=0.0)
            params['salary_technical'] = st.number_input("Technical Salary (£/h)", value=25.0, min_value=0.0)
            params['activity_rejection'] = st.slider("Activity Rejection Factor", 1.0, 1.2, 1.05)

        st.subheader("🏗️ Materials & Sands")
        col1, col2 = st.columns(2)
        with col1:
            params['mold_sand_weight'] = st.number_input("Mold Sand Weight (kg)", value=5.0, min_value=0.0)
            params['mold_sand_cost'] = st.number_input("Mold Sand Cost (£/kg)", value=0.05, min_value=0.0)
            params['core_sand_weight'] = st.number_input("Core Sand Weight (kg)", value=1.0, min_value=0.0)
        with col2:
            params['core_sand_cost'] = st.number_input("Core Sand Cost (£/kg)", value=0.10, min_value=0.0)
            params['sand_recycle_factor'] = st.slider("Sand Recycle Factor", 0.1, 1.0, 0.7)
            params['misc_material_cost'] = st.number_input("Misc. Mat. Cost (£)", value=0.0, min_value=0.0)
        col1, col2 = st.columns(2)
        with col1:
            params['mold_rejection_factor'] = st.slider("Mold Rejection Factor", 1.0, 1.2, 1.05)
        with col2:
            params['core_rejection_factor'] = st.slider("Core Rejection Factor", 1.0, 1.2, 1.05)

        st.subheader("⚡ Energy Parameters")
        col1, col2 = st.columns(2)
        with col1:
            params['energy_cost'] = st.number_input("Energy Cost (£/kWh)", value=0.10, min_value=0.0)
            params['melting_energy'] = st.number_input("Melting Energy (kWh/t)", value=580.0, min_value=0.0)
        with col2:
            params['holding_energy'] = st.number_input("Holding Energy (kWh/t/min)", value=0.4, min_value=0.0)
            params['holding_time'] = st.number_input("Holding Time (min)", value=30.0, min_value=0.0)
            params['other_energy_rate'] = st.number_input("Other Energy (£/kg)", value=0.50, min_value=0.0)

        st.subheader("🛠️ Tooling Parameters")
        col1, col2 = st.columns(2)
        with col1:
            params['software_updates_cost'] = st.number_input("Software Updates (£/yr)", value=5000.0, min_value=0.0)
            params['design_units_produced'] = st.number_input("Design Units Produced", value=50, min_value=1)
        with col2:
            params['tooling_consumables_cost'] = st.number_input("Tooling Consumables (£)", value=200.0, min_value=0.0)
            params['equipment_maintenance_cost'] = st.number_input("Equipment Maintenance (£)", value=1000.0, min_value=0.0)
            params['machining_cost_per_hour'] = st.number_input("Machining Cost (£/h)", value=40.0, min_value=0.0)
            params['machining_time'] = st.number_input("Machining Time (h)", value=2.0, min_value=0.0)

        st.subheader("📊 Overheads")
        col1, col2 = st.columns(2)
        with col1:
            params['admin_percentage'] = st.number_input("Admin Overhead (%)", value=10.0, min_value=0.0)
        with col2:
            params['depr_percentage'] = st.number_input("Depreciation (%)", value=20.0, min_value=0.0)

        st.subheader("🔧 Post-Casting Processes")
        st.write("**Fettling**")
        col1, col2 = st.columns(2)
        with col1:
            params['fettling_labor_hours'] = st.number_input("Fettling Labor Hours", value=0.5, min_value=0.0)
            params['fettling_labor_rate'] = st.number_input("Fettling Labor Rate (£/h)", value=25.0, min_value=0.0)
        with col2:
            params['fettling_equipment_cost'] = st.number_input("Fettling Equipment Cost (£)", value=5.0, min_value=0.0)
        st.write("**Heat Treatment**")
        col1, col2 = st.columns(2)
        with col1:
            params['heat_treatment_energy'] = st.number_input("Heat Treatment Energy (kWh)", value=50.0, min_value=0.0)
            params['heat_treatment_labor_rate'] = st.number_input("Heat Treatment Labor Rate (£/h)", value=30.0, min_value=0.0)
        with col2:
            params['heat_treatment_labor_hours'] = st.number_input("Heat Treatment Labor Hours", value=1.0, min_value=0.0)
        st.write("**Testing & Inspection**")
        col1, col2 = st.columns(2)
        with col1:
            params['ndt_cost_per_part'] = st.number_input("NDT Cost per Part (£)", value=15.0, min_value=0.0)
            params['inspection_labor_hours'] = st.number_input("Final Inspection Hours", value=0.5, min_value=0.0)
        with col2:
            params['inspection_labor_rate'] = st.number_input("Inspection Labor Rate (£/h)", value=25.0, min_value=0.0)
        st.markdown("**Pressure Testing**")
        col1, col2 = st.columns(2)
        with col1:
            params['pressure_testing_labor_hours'] = st.number_input("Pressure Testing Labor Hours", value=0.5, min_value=0.0)
        with col2:
            params['pressure_testing_labor_rate'] = st.number_input("Pressure Testing Labor Rate (£/h)", value=35.0, min_value=0.0)
            params['pressure_testing_equipment_cost'] = st.number_input("Pressure Testing Equipment (£)", value=20.0, min_value=0.0)
        st.markdown("**Radiography & Plating**")
        col1, col2 = st.columns(2)
        with col1:
            params['radiography_cost_per_part'] = st.number_input("Radiography Cost per Part (£)", value=25.0, min_value=0.0)
        with col2:
            params['plating_cost'] = st.number_input("Plating Cost per Part (£)", value=45.0, min_value=0.0)

    # Main content area
    if st.button("🚀 Calculate Total Cost", use_container_width=True):
        with st.spinner("Calculating costs..."):
            try:
                cost_breakdown, post_casting, profit_loss, profit_loss_percent = total_costs(params)
                st.subheader("📊 Cost Analysis")
                tab1, tab2, tab3 = st.tabs(["Summary", "Cost Breakdown", "Post-Casting Details"])
                with tab1:
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.metric("Total Estimated Cost",
                                  f"£{cost_breakdown['Total']:,.2f}",
                                  delta=None)
                        st.metric("Quoted Price",
                                  f"£{params['quote']:,.2f}",
                                  delta=None)
                    with col2:
                        status = "Profit" if profit_loss >= 0 else "Loss"
                        st.metric(f"{status}",
                                  f"£{abs(profit_loss):,.2f} ({profit_loss_percent:.1f}%)",
                                  delta_color="normal" if profit_loss >= 0 else "inverse")
                    st.divider()
                    st.subheader("Cost Distribution")
                    col3, col4 = st.columns([1, 1])
                    with col3:
                        # Horizontal bar chart with colors
                        hbar_fig, hbar_ax = plt.subplots(figsize=(6, 4))
                        labels = [k for k in cost_breakdown.keys() if k not in ['Total', 'Profit/Loss']]
                        sizes = [cost_breakdown[k] for k in labels]
                        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']
                        hbar_ax.barh(labels, sizes, color=colors[:len(labels)])
                        hbar_ax.set_xlabel("Cost (£)")
                        hbar_ax.set_title("Cost Distribution")
                        hbar_ax.grid(True, alpha=0.3)
                        plt.tight_layout()
                        st.pyplot(hbar_fig)
                    with col4:
                        # Vertical bar chart with colors
                        bar_fig, bar_ax = plt.subplots(figsize=(6, 4))
                        bar_ax.bar(labels, sizes, color=colors[:len(labels)])
                        bar_ax.set_ylabel("Cost (£)")
                        bar_ax.set_title("Cost by Category")
                        bar_ax.tick_params(axis='x', rotation=45)
                        bar_ax.grid(True, axis='y', alpha=0.3)
                        plt.tight_layout()
                        st.pyplot(bar_fig)
                with tab2:
                    st.subheader("Detailed Cost Breakdown")
                    df = pd.DataFrame.from_dict(cost_breakdown, orient='index', columns=['£ Amount'])
                    st.dataframe(df.style.format("£{:,.2f}"), height=500)
                    st.download_button(
                        label="📥 Export Cost Report as CSV",
                        data=df.to_csv().encode('utf-8'),
                        file_name=f"casting_cost_report_{params['metal']}_{params['quantity']}pcs.csv",
                        mime="text/csv"
                    )
                with tab3:
                    st.subheader("Post-Casting Process Breakdown")
                    post_df = pd.DataFrame.from_dict(post_casting, orient='index', columns=['£ Amount'])
                    st.dataframe(post_df.style.format("£{:,.2f}"))
                    # Post-casting bar chart with colors
                    fig, ax = plt.subplots(figsize=(8, 4))
                    post_labels = list(post_casting.keys())
                    post_values = list(post_casting.values())
                    ax.bar(post_labels, post_values, color=colors[:len(post_labels)])
                    ax.set_ylabel("Cost (£)")
                    ax.set_title("Post-Casting Process Costs")
                    ax.tick_params(axis='x', rotation=45)
                    ax.grid(True, axis='y', alpha=0.3)
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()
                    st.pyplot(fig)
            except Exception as e:
                st.error(f"Error in calculation: {str(e)}")

if __name__ == "__main__":
    main()
