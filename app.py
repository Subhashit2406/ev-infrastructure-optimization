import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import json
import glob

# Page Config
st.set_page_config(
    page_title="EV Infrastructure Optimization",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
PROCESSED_DIR = "data/processed"
RESULTS_DIR = "results"

# Load Data
@st.cache_data
def load_data():
    try:
        sales = pd.read_csv(os.path.join(PROCESSED_DIR, "ev_sales_processed.csv"))
    except:
        sales = None
        
    try:
        stations = pd.read_csv(os.path.join(PROCESSED_DIR, "stations_processed.csv"))
    except:
        stations = None
        
    try:
        usage = pd.read_csv(os.path.join(PROCESSED_DIR, "usage_processed.csv"))
    except:
        usage = None
    
    return sales, stations, usage

# Sidebar
st.sidebar.title("⚡ EV Dashboard")
page = st.sidebar.radio("Navigate", ["Overview", "Forecasting", "Geospatial Analysis", "Grid Load Optimization", "Financial Analysis"])

# Main App
sales_df, stations_df, usage_df = load_data()

if page == "Overview":
    st.title("🇮🇳 EV Infrastructure Optimization - India")
    st.markdown("### Strategic Analysis & Planning System")
    
    col1, col2, col3 = st.columns(3)
    if sales_df is not None:
        col1.metric("Total EV Sales Recorded", f"{sales_df['ev_sales_count'].sum():,}")
    if stations_df is not None:
        col2.metric("Active Charging Stations", f"{len(stations_df):,}")
    if usage_df is not None:
        col3.metric("Charging Sessions Logged", f"{len(usage_df):,}")
        
    st.image("https://images.unsplash.com/photo-1593941707882-a5bba14938c7?ixlib=rb-1.2.1&auto=format&fit=crop&w=1950&q=80", use_column_width=True)
    st.info("This system uses a hybrid dataset (Real + Synthetic) to optimize EV infrastructure placement, forecast demand, and analyze grid impact.")

elif page == "Forecasting":
    st.title("📈 Demand Forecasting")
    st.write("Predicted EV sales trend using ARIMA/XGBoost.")
    
    if os.path.exists(os.path.join(RESULTS_DIR, "phase1_forecasting", "actual_vs_predicted.png")):
        st.image(os.path.join(RESULTS_DIR, "phase1_forecasting", "actual_vs_predicted.png"), caption="Sales Forecast Model", use_column_width=True)
    
    if sales_df is not None:
        st.subheader("Historical Sales Data")
        st.line_chart(sales_df.set_index("date")["ev_sales_count"])

elif page == "Geospatial Analysis":
    st.title("🗺️ Network Planning & Clustering")
    
    if stations_df is not None:
        st.map(stations_df[["latitude", "longitude"]].dropna())
        
    st.subheader("Regional White Space Analysis")
    if os.path.exists("./interactive_plots/station_map.html"):
        with open("./interactive_plots/station_map.html", 'r', encoding='utf-8') as f:
            html = f.read()
        st.components.v1.html(html, height=600, scrolling=True)
    else:
        st.warning("Interactive map not found. Run the pipeline first.")

elif page == "Grid Load Optimization":
    st.title("⚡ Grid Load Optimization")
    
    st.write("Optimal charging schedule to minimize peak grid impact.")
    
    if os.path.exists("./interactive_plots/grid_load_profile.html"):
        with open("./interactive_plots/grid_load_profile.html", 'r', encoding='utf-8') as f:
            html = f.read()
        st.components.v1.html(html, height=600, scrolling=True)
    
    if os.path.exists(os.path.join(RESULTS_DIR, "phase3_optimization", "optimization_results.json")):
        with open(os.path.join(RESULTS_DIR, "phase3_optimization", "optimization_results.json")) as f:
            res = json.load(f)
        st.success(f"Optimized Peak Load: {res.get('optimized_peak_kw', 0):.2f} kW")
        st.error(f"Baseline Peak Load: {res.get('baseline_peak_kw', 0):.2f} kW")

elif page == "Financial Analysis":
    st.title("💰 ROI & Carbon Impact")
    
    if os.path.exists(os.path.join(RESULTS_DIR, "phase4_financial", "financial_results.json")):
        with open(os.path.join(RESULTS_DIR, "phase4_financial", "financial_results.json")) as f:
            fin_data = json.load(f)
        
        # Create a selection box for different scenarios
        scenarios = [f"{item['state']} - {item['station_type'].upper()}" for item in fin_data]
        selected_scenario = st.selectbox("Select Scenario", scenarios)
        
        # Find the selected data
        fin = next(item for item in fin_data if f"{item['state']} - {item['station_type'].upper()}" == selected_scenario)
        
        st.markdown(f"### Financial Summary: {selected_scenario}")
        
        c1, c2 = st.columns(2)
        c1.metric("Net Present Value (NPV)", f"₹ {fin.get('npv_inr', 0):,.2f}")
        c2.metric("Payback Period", f"{fin.get('breakeven_months', 0)/12:.1f} Years")
        
        c3, c4 = st.columns(2)
        c3.metric("IRR", f"{fin.get('irr_pct', 0):.1f}%")
        c4.metric("Setup Cost", f"₹ {fin.get('setup_cost_inr', 0):,.0f}")

        st.subheader("Carbon Emissions Saved")
        st.metric("CO2 Reduction", f"{fin['environmental_impact'].get('annual_co2_saved_tons', 0):.2f} Tons", delta="Positive Impact")
        
        # Cashflow Chart
        st.subheader("Projected Cashflows (10 Years)")
        cf_df = pd.DataFrame({
            "Year": range(len(fin['yearly_cashflows'])),
            "Cashflow": fin['yearly_cashflows'],
            "Cumulative": fin['yearly_cumulative']
        })
        st.line_chart(cf_df.set_index("Year")[["Cumulative"]])
