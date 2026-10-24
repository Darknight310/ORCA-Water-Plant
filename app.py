import streamlit as st
import pandas as pd
import plotly.express as px

# Import modular components
from styles import apply_custom_styles
from database import load_database, init_session_state
from functions import render_sales_form, render_customer_form

# Page Configuration
st.set_page_config(
    page_title="ORCA Plant Management System",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Styling
apply_custom_styles()

# Load Database & Session State
try:
    raw_db = load_database()
    init_session_state(raw_db)
except Exception as e:
    st.error(f"⚠️ Error reading database file: {e}")
    st.stop()

# Top Header Layout
st.markdown("""
    <div class="header-container">
        <div>
            <div class="header-subtitle">ORCA PLANT MANAGEMENT SYSTEM</div>
            <div class="header-title">Executive Dashboard (P&L Summary)</div>
        </div>
        <div style="background-color: #1E293B; padding: 8px 16px; border-radius: 8px; color: #38BDF8; font-weight: 600; font-size: 0.9rem; border: 1px solid #334155;">
            🟢 Database Synced (v3.0)
        </div>
    </div>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.markdown("<h2 style='color: #FFFFFF; font-size: 1.2rem;'>💧 ORCA PLANT</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='color: #94A3B8; font-size: 0.8rem; margin-top: -10px;'>MANAGEMENT SYSTEM</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

app_mode = st.sidebar.radio("Navigation", [
    "📊 Executive Dashboard", 
    "🛍️ Sales Orders & Invoices", 
    "📦 Inventory & Raw Materials", 
    "👥 Customer Directory", 
    "💸 Expenses & Owner Draws"
], label_visibility="collapsed")

# ==========================================
# 1. EXECUTIVE DASHBOARD
# ==========================================
if app_mode == "📊 Executive Dashboard":
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Gross Sales", value="PKR 192,320.00", delta="142 Invoiced Orders")
    with col2:
        st.metric(label="Total Discounts", value="PKR 6,190.00", delta="Rate Adjustments")
    with col3:
        st.metric(label="Net Sales Revenue", value="PKR 186,130.00", delta="Fully Reconciled")
    with col4:
        st.metric(label="Net Profit / Cash Flow", value="PKR 17,966.46", delta="After Draws & Expenses")

    col5, col6, col7 = st.columns(3)
    with col5:
        st.metric(label="Cost of Goods Sold (COGS)", value="PKR 136,053.54")
    with col6:
        st.metric(label="Direct Operating Expenses", value="PKR 11,760.00")
    with col7:
        st.metric(label="Owner Draws", value="PKR 20,350.00")

    st.markdown("---")
    
    col_left, col_right = st.columns([3, 2], gap="large")
    
    with col_left:
        st.markdown("""
            <div style="background-color: #111827; border: 1px solid #1F2937; border-radius: 12px; padding: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h3 style="color: #FFFFFF; font-size: 1.15rem; font-weight: 700; margin: 0;">Master Profit & Loss Breakdown</h3>
                    <span style="background-color: #1E293B; color: #38BDF8; font-size: 0.75rem; font-weight: 600; padding: 4px 12px; border-radius: 6px; border: 1px solid #334155;">Official Baseline</span>
                </div>
                <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
                    <thead>
                        <tr style="border-bottom: 1px solid #1F2937; color: #94A3B8; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px;">
                            <th style="text-align: left; padding: 0 12px 10px 12px;">Financial Category</th>
                            <th style="text-align: right; padding: 0 12px 10px 12px;">Amount (PKR)</th>
                            <th style="text-align: right; padding: 0 12px 10px 12px;">% of Revenue</th>
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
    st.subheader("🛍️ Sales Orders & Invoicing Control")
    render_sales_form()
    
    search_query = st.text_input("🔍 Search Sales Records:")
    df_sales = st.session_state.sales_df
    if search_query:
        str_cols = df_sales.select_dtypes(include=['object']).columns
        mask = df_sales[str_cols].apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        df_sales = df_sales[mask]
    st.dataframe(df_sales, use_container_width=True, hide_index=True)

# ==========================================
# 3. INVENTORY & RAW MATERIALS
# ==========================================
elif app_mode == "📦 Inventory & Raw Materials":
    st.subheader("📦 Finished Goods & Raw Materials Ledger")
    tab1, tab2 = st.tabs(["Finished Goods", "Raw Materials"])
    with tab1:
        st.dataframe(st.session_state.products_df, use_container_width=True, hide_index=True)
    with tab2:
        st.dataframe(st.session_state.raw_materials_df, use_container_width=True, hide_index=True)

# ==========================================
# 4. CUSTOMER DIRECTORY
# ==========================================
elif app_mode == "👥 Customer Directory":
    st.subheader("👥 Active Customer Accounts Directory")
    render_customer_form()
    st.dataframe(st.session_state.customers_df, use_container_width=True, hide_index=True)

# ==========================================
# 5. EXPENSES & OWNER DRAWS
# ==========================================
elif app_mode == "💸 Expenses & Owner Draws":
    st.subheader("💸 Operating Expenses & Owner Withdrawals")
    tab1, tab2 = st.tabs(["Operating Expenses", "Owner Draws"])
    with tab1:
        st.dataframe(st.session_state.expenses_df, use_container_width=True, hide_index=True)
    with tab2:
        st.dataframe(st.session_state.draws_df, use_container_width=True, hide_index=True)
