import streamlit as st
import pandas as pd
import plotly.express as px
import time

# Import modular components
from styles import apply_custom_styles
from database import load_database, init_session_state
from functions import render_sales_form, render_customer_form, convert_pnl_to_excel

# Page Configuration
st.set_page_config(
    page_title="ORCA Water Company Management System",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Styling
apply_custom_styles()

# ==========================================
# SPLASH SCREEN / LOADING ANIMATION (ON FIRST LOAD)
# ==========================================
if "loaded" not in st.session_state:
    st.session_state.loaded = False

if not st.session_state.loaded:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("""
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 70vh; text-align: center;">
                <div style="font-size: 3rem; margin-bottom: 15px; animation: bounce 1.5s infinite;">💧</div>
                <h2 style='color: #FFFFFF; font-size: 1.8rem; font-weight: 800; margin-bottom: 5px;'>ORCA WATER COMPANY</h2>
                <p style='color: #38BDF8; font-size: 0.9rem; font-weight: 600; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 25px;'>Initializing Plant Management System...</p>
                
                <div style="width: 280px; background-color: #1F2937; border-radius: 20px; overflow: hidden; padding: 3px; border: 1px solid #334155;">
                    <div id="progress-bar" style="width: 0%; height: 12px; background: linear-gradient(90deg, #38BDF8, #34D399); border-radius: 15px; transition: width 0.4s ease;"></div>
                </div>
            </div>
            
            <style>
            @keyframes bounce {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-10px); }
            }
            </style>
        """, unsafe_allow_html=True)
        
        progress_bar = st.progress(0)
        for percent_complete in range(100):
            time.sleep(0.01)
            progress_bar.progress(percent_complete + 1)
        
        progress_bar.empty()
        time.sleep(0.2)
    
    st.session_state.loaded = True
    st.rerun()

# Load Database & Session State
try:
    raw_db = load_database()
    init_session_state(raw_db)
except Exception as e:
    st.error(f"⚠️ Error reading database file: {e}")
    st.stop()

# Initialize Navigation State
if "app_mode" not in st.session_state:
    st.session_state.app_mode = "📊 Executive Dashboard"

nav_options = [
    "📊 Executive Dashboard", 
    "🛍️ Sales Orders & Invoices", 
    "📦 Inventory & Raw Materials", 
    "👥 Customer Directory", 
    "💸 Expenses & Owner Draws"
]

# ==========================================
# SIDEBAR NAVIGATION & BRANDING
# ==========================================
st.sidebar.markdown("""
    <h2 style='color: #FFFFFF; font-size: 1.1rem; font-weight: 800; margin: 0; letter-spacing: -0.5px;'>ORCA WATER COMPANY</h2>
    <p style='color: #94A3B8; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 2px;'>MANAGEMENT SYSTEM</p>
    <hr style='border: 1px solid #1E293B; margin: 15px 0 15px 0;'>
    <p style='color: #94A3B8; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; margin-bottom: 8px;'>Quick Navigation</p>
""", unsafe_allow_html=True)

for option in nav_options:
    if st.sidebar.button(option, use_container_width=True, key=f"side_{option}"):
        if st.session_state.app_mode != option:
            st.session_state.app_mode = option
            st.rerun()

app_mode = st.session_state.app_mode

# ==========================================
# TOP HEADER & HORIZONTAL NAVIGATION TABS
# ==========================================
st.markdown("""
    <div style="background-color: #111827; border: 1px solid #1F2937; border-radius: 12px; padding: 16px 24px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div style="color: #38BDF8; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 2px;">ORCA WATER COMPANY</div>
            <div style="color: #FFFFFF; font-size: 1.35rem; font-weight: 800; letter-spacing: -0.5px;">Enterprise Management System</div>
        </div>
        <div style="background-color: #1E293B; color: #34D399; font-size: 0.8rem; font-weight: 600; padding: 6px 14px; border-radius: 8px; border: 1px solid #334155;">
            🟢 Live Database Active
        </div>
    </div>
""", unsafe_allow_html=True)

top_cols = st.columns(5)
for i, opt in enumerate(nav_options):
    with top_cols[i]:
        is_active = (app_mode == opt)
        btn_label = f"📌 {opt.split(' ')[1]}" if is_active else opt.split(' ', 1)[1]
        if st.button(btn_label, use_container_width=True, key=f"top_tab_{i}"):
            if st.session_state.app_mode != opt:
                st.session_state.app_mode = opt
                st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 1. EXECUTIVE DASHBOARD
# ==========================================
if app_mode == "📊 Executive Dashboard":
    st.markdown("""
        <div class="header-container">
            <div class="header-subtitle">MODULE VIEW</div>
            <div class="header-title">Executive Dashboard (P&L Summary)</div>
        </div>
    """, unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(label="Gross Sales", value="PKR 192,320", delta="142 Orders")
    with m2:
        st.metric(label="Total Discounts", value="PKR 6,190", delta="Adjustments")
    with m3:
        st.metric(label="Net Sales Revenue", value="PKR 186,130", delta="Reconciled")
    with m4:
        st.metric(label="Net Profit / Cash Flow", value="PKR 17,966", delta="Net Return")

    m5, m6, m7 = st.columns(3)
    with m5:
        st.metric(label="Cost of Goods Sold (COGS)", value="PKR 136,053.54")
    with m6:
        st.metric(label="Direct Operating Expenses", value="PKR 11,760.00")
    with m7:
        st.metric(label="Owner Draws", value="PKR 20,350.00")

    st.markdown("---")
    
    col_left, col_right = st.columns([3, 2], gap="large")
    
    with col_left:
        col_t1, col_t2, col_t3 = st.columns([3, 1.2, 1.2])
        with col_t1:
            st.markdown("<h3 style='color: #FFFFFF; font-size: 1.15rem; font-weight: 700; margin: 0;'>Master Profit & Loss Breakdown</h3>", unsafe_allow_html=True)
        with col_t2:
            st.markdown("<div style='background-color: #1E293B; color: #38BDF8; font-size: 0.75rem; font-weight: 600; padding: 6px 10px; border-radius: 6px; border: 1px solid #334155; text-align: center;'>Official Baseline</div>", unsafe_allow_html=True)
        with col_t3:
            excel_data = convert_pnl_to_excel()
            st.download_button(
                label="📥 Export Excel",
                data=excel_data,
                file_name="ORCA_Master_PnL_Breakdown.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        st.markdown("""
            <div style="background-color: #111827; border: 1px solid #1F2937; border-radius: 12px; padding: 20px; margin-top: 10px;">
                <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
                    <thead>
                        <tr style="border-bottom: 2px solid #334155; color: #F8FAFC; font-size: 0.85rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.8px;">
                            <th style="text-align: left; padding: 0 12px 12px 12px;">Financial Category</th>
                            <th style="text-align: right; padding: 0 12px 12px 12px;">Amount (PKR)</th>
                            <th style="text-align: right; padding: 0 12px 12px 12px;">% of Revenue</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr style="border-bottom: 1px solid #1F2937;">
                            <td style="padding: 12px; color: #FFFFFF; font-weight: 600;">Gross Sales Revenue</td>
                            <td style="text-align: right; padding: 12px; color: #FFFFFF; font-weight: 600;">192,320.00</td>
                            <td style="text-align: right; padding: 12px; color: #94A3B8;">103.3%</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #1F2937;">
                            <td style="padding: 12px; color: #FBBF24;">Less: Total Discounts Allowed</td>
                            <td style="text-align: right; padding: 12px; color: #FBBF24;">-6,190.00</td>
                            <td style="text-align: right; padding: 12px; color: #FBBF24;">-3.3%</td>
                        </tr>
                        <tr style="background-color: #162032; border-bottom: 1px solid #1F2937;">
                            <td style="padding: 12px; color: #34D399; font-weight: 600;">Net Sales Revenue</td>
                            <td style="text-align: right; padding: 12px; color: #34D399; font-weight: 600;">186,130.00</td>
                            <td style="text-align: right; padding: 12px; color: #34D399; font-weight: 600;">100.0%</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #1F2937;">
                            <td style="padding: 12px; color: #F87171;">Less: Cost of Goods Sold (COGS)</td>
                            <td style="text-align: right; padding: 12px; color: #F87171;">-136,053.54</td>
                            <td style="text-align: right; padding: 12px; color: #F87171;">-73.1%</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #1F2937;">
                            <td style="padding: 12px; color: #FFFFFF; font-weight: 600;">Gross Profit</td>
                            <td style="text-align: right; padding: 12px; color: #38BDF8; font-weight: 600;">50,076.46</td>
                            <td style="text-align: right; padding: 12px; color: #FFFFFF; font-weight: 600;">26.9%</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #1F2937;">
                            <td style="padding: 12px; color: #FBBF24;">Less: Direct Operating Expenses</td>
                            <td style="text-align: right; padding: 12px; color: #FBBF24;">-11,760.00</td>
                            <td style="text-align: right; padding: 12px; color: #FBBF24;">-6.3%</td>
                        </tr>
                        <tr style="background-color: #162032; border-bottom: 1px solid #1F2937;">
                            <td style="padding: 12px; color: #34D399; font-weight: 600;">Operating Net Profit</td>
                            <td style="text-align: right; padding: 12px; color: #34D399; font-weight: 600;">38,316.46</td>
                            <td style="text-align: right; padding: 12px; color: #34D399; font-weight: 600;">20.6%</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #1F2937;">
                            <td style="padding: 12px; color: #C084FC;">Less: Owner Personal Draws</td>
                            <td style="text-align: right; padding: 12px; color: #C084FC;">-20,350.00</td>
                            <td style="text-align: right; padding: 12px; color: #C084FC;">-10.9%</td>
                        </tr>
                        <tr style="background-color: #1E2640;">
                            <td style="padding: 12px; color: #38BDF8; font-weight: 700;">Net Retained Cash Flow</td>
                            <td style="text-align: right; padding: 12px; color: #FFFFFF; font-weight: 700;">17,966.46</td>
                            <td style="text-align: right; padding: 12px; color: #38BDF8; font-weight: 700;">9.7%</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown("### 📊 Cost & Expense Breakdown")
        st.markdown("<p style='color: #94A3B8; font-size: 0.85rem; margin-top: -5px;'>Visual allocation of plant capital outflows.</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        chart_data = pd.DataFrame({
            "Category": ["COGS", "Operating Expenses", "Owner Draws", "Net Profit"],
            "Amount": [136053.54, 11760.00, 20350.00, 17966.46]
        })
        
        fig = px.pie(
            chart_data, values="Amount", names="Category", hole=0.55, 
            color_discrete_sequence=["#38BDF8", "#FBBF24", "#C084FC", "#34D399"]
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", 
            font_color="#FFFFFF", height=340, margin=dict(t=10, b=10, l=10, r=10), 
            legend=dict(orientation="h", y=-0.15, x=0.05)
        )
        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 2. SALES ORDERS & INVOICES
# ==========================================
elif app_mode == "🛍️ Sales Orders & Invoices":
    st.markdown("""
        <div class="header-container">
            <div class="header-subtitle">MODULE VIEW</div>
            <div class="header-title">Sales Orders & Invoicing Control</div>
        </div>
    """, unsafe_allow_html=True)
    
    render_sales_form()
    
    df_sales = st.session_state.sales_df
    
    # Calculate dynamic totals for the summary tile
    total_orders = len(df_sales)
    total_qty = df_sales["Qty"].sum() if "Qty" in df_sales.columns else 0
    
    if "Total (PKR)" in df_sales.columns:
        total_revenue = pd.to_numeric(df_sales["Total (PKR)"].astype(str).str.replace(",", ""), errors='coerce').sum()
    else:
        total_revenue = 0.0

    # Summary Tile Card before the table
    st.markdown(f"""
        <div style="background-color: #111827; border: 1px solid #1F2937; border-radius: 12px; padding: 18px 24px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="color: #94A3B8; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">Live Sales Summary</div>
                <div style="color: #FFFFFF; font-size: 1.2rem; font-weight: 800; margin-top: 4px;">Total Orders: <span style="color: #38BDF8;">{total_orders}</span> &nbsp;|&nbsp; Total Qty Sold: <span style="color: #34D399;">{total_qty:,.0f}</span></div>
            </div>
            <div style="text-align: right;">
                <div style="color: #94A3B8; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">Total Revenue Generated</div>
                <div style="color: #38BDF8; font-size: 1.35rem; font-weight: 800; margin-top: 2px;">PKR {total_revenue:,.2f}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    search_query = st.text_input("🔍 Search Sales Records:")
    if search_query:
        str_cols = df_sales.select_dtypes(include=['object']).columns
        mask = df_sales[str_cols].apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        df_sales = df_sales[mask]
        
    st.dataframe(df_sales, use_container_width=True, hide_index=True)

# ==========================================
# 3. INVENTORY & RAW MATERIALS
# ==========================================
elif app_mode == "📦 Inventory & Raw Materials":
    st.markdown("""
        <div class="header-container">
            <div class="header-subtitle">MODULE VIEW</div>
            <div class="header-title">Inventory & Raw Materials Ledger</div>
        </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Finished Goods", "Raw Materials"])
    with tab1:
        st.dataframe(st.session_state.products_df, use_container_width=True, hide_index=True)
    with tab2:
        st.dataframe(st.session_state.raw_materials_df, use_container_width=True, hide_index=True)

# ==========================================
# 4. CUSTOMER DIRECTORY
# ==========================================
elif app_mode == "👥 Customer Directory":
    st.markdown("""
        <div class="header-container">
            <div class="header-subtitle">MODULE VIEW</div>
            <div class="header-title">Active Customer Accounts Directory</div>
        </div>
    """, unsafe_allow_html=True)
    
    render_customer_form()
    st.dataframe(st.session_state.customers_df, use_container_width=True, hide_index=True)

# ==========================================
# 5. EXPENSES & OWNER DRAWS
# ==========================================
elif app_mode == "💸 Expenses & Owner Draws":
    st.markdown("""
        <div class="header-container">
            <div class="header-subtitle">MODULE VIEW</div>
            <div class="header-title">Operating Expenses & Owner Withdrawals</div>
        </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Operating Expenses", "Owner Draws"])
    with tab1:
        st.dataframe(st.session_state.expenses_df, use_container_width=True, hide_index=True)
    with tab2:
        st.dataframe(st.session_state.draws_df, use_container_width=True, hide_index=True)
