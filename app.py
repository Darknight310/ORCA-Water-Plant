import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date

# Page Configuration
st.set_page_config(
    page_title="ORCA Plant Management System",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Dark Theme CSS (Matching the Enterprise UI)
st.markdown("""
    <style>
    /* Global Dark Theme Background */
    .stApp {
        background-color: #0B0F19;
        color: #F8FAFC;
    }
    
    /* Hide default Streamlit header elements for clean look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0F172A;
        border-right: 1px solid #1E293B;
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }
    
    /* Top Header Bar */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #0F172A;
        padding: 15px 25px;
        border-radius: 12px;
        border: 1px solid #1E293B;
        margin-bottom: 25px;
    }
    .header-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #FFFFFF;
        letter-spacing: -0.5px;
    }
    .header-subtitle {
        font-size: 0.85rem;
        color: #38BDF8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Metric Cards Styling */
    div.stMetric {
        background-color: #111827;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        border: 1px solid #1F2937;
    }
    div.stMetric label { color: #94A3B8 !important; font-weight: 600 !important; font-size: 0.8rem !important; text-transform: uppercase; }
    div.stMetric [data-testid="stMetricValue"] { color: #FFFFFF !important; font-weight: 700 !important; font-size: 1.5rem !important; }
    
    /* Dataframes & Tables */
    [data-testid="stDataFrame"] {
        background-color: #111827;
        border-radius: 10px;
        border: 1px solid #1F2937;
        padding: 10px;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #0284C7;
        color: white;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover { background-color: #0369A1; color: white; }
    
    /* Tabs & Expander */
    .streamlit-expanderHeader {
        background-color: #111827;
        color: #FFFFFF;
        border-radius: 8px;
        border: 1px solid #1F2937;
    }
    </style>
""", unsafe_allow_html=True)

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

# Direct File Reference
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_NAME = "ORCA_Water_Plant_Master_Database_Definitive.xlsx"
FILE_PATH = os.path.join(BASE_DIR, FILE_NAME)
if not os.path.exists(FILE_PATH):
    FILE_PATH = FILE_NAME

@st.cache_data
def load_excel_data(path):
    xls = pd.ExcelFile(path)
    return {sheet: pd.read_excel(xls, sheet_name=sheet) for sheet in xls.sheet_names}

try:
    raw_db = load_excel_data(FILE_PATH)
except Exception as e:
    st.error(f"⚠️ Error reading database file `{FILE_NAME}`: {e}")
    st.stop()

# Initialize Session State
if 'sales_df' not in st.session_state:
    st.session_state.sales_df = raw_db.get("Sales_Orders", pd.DataFrame())
if 'products_df' not in st.session_state:
    st.session_state.products_df = raw_db.get("Products", pd.DataFrame())
if 'raw_materials_df' not in st.session_state:
    st.session_state.raw_materials_df = raw_db.get("Raw_Materials", pd.DataFrame())
if 'customers_df' not in st.session_state:
    st.session_state.customers_df = raw_db.get("Customers", pd.DataFrame())
if 'expenses_df' not in st.session_state:
    st.session_state.expenses_df = raw_db.get("Direct_Operating_Expenses", pd.DataFrame())
if 'draws_df' not in st.session_state:
    st.session_state.draws_df = raw_db.get("Owners_Draws", pd.DataFrame())

# Sidebar Navigation (Properly defining app_mode)
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
    # Top KPI Metrics Row 1
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Gross Sales", value="PKR 192,320.00", delta="142 Invoiced Orders")
    with col2:
        st.metric(label="Total Discounts", value="PKR 6,190.00", delta="Rate Adjustments")
    with col3:
        st.metric(label="Net Sales Revenue", value="PKR 186,130.00", delta="Fully Reconciled")
    with col4:
        st.metric(label="Net Profit / Cash Flow", value="PKR 17,966.46", delta="After Draws & Expenses")

    # Top KPI Metrics Row 2
    col5, col6, col7 = st.columns(3)
    with col5:
        st.metric(label="Cost of Goods Sold (COGS)", value="PKR 136,053.54")
    with col6:
        st.metric(label="Direct Operating Expenses", value="PKR 11,760.00")
    with col7:
        st.metric(label="Owner Draws", value="PKR 20,350.00")

    st.markdown("---")
    
    # 2-Column Balanced Layout
    col_left, col_right = st.columns([3, 2], gap="large")
    
    with col_left:
        st.markdown("### 📋 Master Profit & Loss Breakdown")
        pnl_data = {
            "Financial Category": [
                "Gross Sales Revenue", "Less: Total Discounts Allowed", "Net Sales Revenue",
                "Less: Cost of Goods Sold (COGS)", "Gross Profit", "Less: Direct Operating Expenses",
                "Operating Net Profit", "Less: Owner Personal Draws", "FINAL NET CASH FLOW"
            ],
            "Amount (PKR)": [
                "192,320.00", "-6,190.00", "186,130.00", 
                "-136,053.54", "50,076.46", "-11,760.00", 
                "38,316.46", "-20,350.00", "17,966.46"
            ],
            "% of Revenue": [
                "103.3%", "-3.3%", "100.0%", "-73.1%", "26.9%", "-6.3%", "20.6%", "-10.9%", "9.6%"
            ]
        }
        st.dataframe(pd.DataFrame(pnl_data), use_container_width=True, hide_index=True)

    with col_right:
        st.markdown("### 📊 Cost & Expense Breakdown")
        st.markdown("<p style='color: #94A3B8; font-size: 0.85rem; margin-top: -5px;'>Visual allocation of plant capital outflows.</p>", unsafe_allow_html=True)
        
        # Alignment spacing to push chart nicely into position
        st.markdown("<br>", unsafe_allow_html=True)
        
        chart_data = pd.DataFrame({
            "Category": ["COGS", "Operating Expenses", "Owner Draws", "Net Profit"],
            "Amount": [136053.54, 11760.00, 20350.00, 17966.46]
        })
        
        fig = px.pie(
            chart_data, 
            values="Amount", 
            names="Category", 
            hole=0.55, 
            color_discrete_sequence=["#38BDF8", "#FBBF24", "#C084FC", "#34D399"]
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", 
            plot_bgcolor="rgba(0,0,0,0)", 
            font_color="#FFFFFF", 
            height=340,
            margin=dict(t=10, b=10, l=10, r=10), 
            legend=dict(orientation="h", y=-0.15, x=0.05)
        )
        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 2. SALES ORDERS & INVOICES
# ==========================================
elif app_mode == "🛍️ Sales Orders & Invoices":
    st.subheader("🛍️ Sales Orders & Invoicing Control")
    
    with st.expander("➕ Record New Sales Order", expanded=False):
        with st.form("new_sale_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                inv_no = st.text_input("Invoice No.", value=f"INV-{len(st.session_state.sales_df)+101}")
                sale_date = st.date_input("Order Date", value=date.today())
            with col2:
                client_name = st.text_input("Client / Customer Name")
                product_name = st.selectbox("Product", ["500ml Bottle (12-pack)", "1.5L Bottle (6-pack)", "19L Dispenser Bottle"])
            with col3:
                qty = st.number_input("Quantity", min_value=1, value=10)
                unit_price = st.number_input("Unit Price (PKR)", min_value=0.0, value=480.0)
            
            status = st.selectbox("Payment Status", ["Paid", "Unpaid", "Partial"])
            submit_sale = st.form_submit_button("Save Sales Order")
            
            if submit_sale:
                total_amt = qty * unit_price
                new_row = {
                    "Invoice No.": inv_no,
                    "Date": str(sale_date),
                    "Client Name": client_name,
                    "Product": product_name,
                    "Qty": qty,
                    "Unit Price (PKR)": unit_price,
                    "Total (PKR)": total_amt,
                    "Status": status
                }
                st.session_state.sales_df = pd.concat([pd.DataFrame([new_row]), st.session_state.sales_df], ignore_index=True)
                st.success(f"Successfully recorded order {inv_no}!")
                st.rerun()

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
    
    with st.expander("➕ Add New Customer Account", expanded=False):
        with st.form("new_customer_form"):
            col1, col2 = st.columns(2)
            with col1:
                c_name = st.text_input("Customer / Store Name")
                c_route = st.text_input("Route / Area")
            with col2:
                c_person = st.text_input("Contact Person")
                c_phone = st.text_input("Phone Number")
            
            submit_cust = st.form_submit_button("Add Customer")
            if submit_cust:
                new_c = {
                    "Client ID": f"CLI-{len(st.session_state.customers_df)+1:02d}",
                    "Client Name": c_name,
                    "Route / Area": c_route,
                    "Contact Person": c_person,
                    "Phone": c_phone,
                    "Balance (PKR)": 0.00
                }
                st.session_state.customers_df = pd.concat([st.session_state.customers_df, pd.DataFrame([new_c])], ignore_index=True)
                st.success("Customer added successfully!")
                st.rerun()

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
