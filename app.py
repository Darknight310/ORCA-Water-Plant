import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Page Configuration
st.set_page_config(
    page_title="ORCA Water Plant Management System",
    page_icon="💧",
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E293B; margin-bottom: 0px; }
    .sub-header { font-size: 1.1rem; color: #64748B; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">💧 ORCA Water Plant Management System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Reconciled Master Financial & Operational Dashboard | Narowal Plant</div>', unsafe_allow_html=True)

# Locate Master Excel Database File Path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_NAME = "ORCA_Water_Plant_Master_Database_Definitive_3.xlsx"
FILE_PATH = os.path.join(BASE_DIR, FILE_NAME)

if not os.path.exists(FILE_PATH):
    FILE_PATH = FILE_NAME

@st.cache_data
def load_all_sheets(path):
    xls = pd.ExcelFile(path)
    sheet_data = {}
    for sheet_name in xls.sheet_names:
        sheet_data[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name)
    return sheet_data

try:
    db = load_all_sheets(FILE_PATH)
    st.sidebar.success("✅ Database Connected: Live Master Sheets Loaded")
except Exception as e:
    st.error(f"⚠️ Error reading database: {e}")
    st.stop()

# Sidebar Navigation
st.sidebar.title("📌 Navigation")
app_mode = st.sidebar.radio("Go to:", [
    "📊 Executive P&L Dashboard", 
    "🛍️ Sales Orders & Invoicing", 
    "📦 Finished Goods & Inventory", 
    "🧪 Raw Materials Tracker", 
    "👥 Customer Directory", 
    "💸 Expenses & Owner Draws"
])

# 1. Executive P&L Dashboard
if app_mode == "📊 Executive P&L Dashboard":
    st.subheader("Executive Financial Performance (P&L Summary)")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Gross Sales Revenue", value="PKR 192,320.00")
    with col2:
        st.metric(label="Total Discounts Allowed", value="PKR 6,190.00")
    with col3:
        st.metric(label="Net Sales Revenue", value="PKR 186,130.00")
    with col4:
        st.metric(label="Net Plant Cash Flow", value="PKR 17,966.46", delta="Profitable")

    st.markdown("---")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("### 📋 P&L Breakdown")
        if "Dashboard_PL" in db:
            st.dataframe(db["Dashboard_PL"], use_container_width=True, hide_index=True)
        else:
            pnl_data = {
                "P&L Category": [
                    "Total Gross Sales Revenue", "Less: Total Discounts Allowed", "Net Sales Revenue",
                    "Less: Cost of Goods Sold (COGS)", "PRODUCT GROSS MARGIN", "Less: Direct Plant Operating Expenses",
                    "GROSS PROFIT", "Less: Indirect Expenses (Owner Draws)", "NET PROFIT / CASH FLOW"
                ],
                "Amount (PKR)": [
                    "192,320.00", "-6,190.00", "186,130.00", 
                    "136,053.54", "50,076.46", "11,760.00", 
                    "38,316.46", "20,350.00", "17,966.46"
                ]
            }
            st.dataframe(pd.DataFrame(pnl_data), use_container_width=True, hide_index=True)

    with col_right:
        st.markdown("### 📊 Cost & Profit Distribution")
        chart_data = pd.DataFrame({
            "Category": ["COGS", "Operating Expenses", "Owner Draws", "Net Profit"],
            "Amount": [136053.54, 11760.00, 20350.00, 17966.46]
        })
        fig = px.pie(chart_data, values="Amount", names="Category", title="Financial Allocation Breakdown", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

# 2. Sales Orders & Invoicing
elif app_mode == "🛍️ Sales Orders & Invoicing":
    st.subheader("All Itemized Sales Orders (From Master Database)")
    sheet_key = "Sales_Orders" if "Sales_Orders" in db else list(db.keys())[0]
    df_sales = db[sheet_key]
    
    search_query = st.text_input("🔍 Search sales records...")
    if search_query:
        str_cols = df_sales.select_dtypes(include=['object']).columns
        mask = df_sales[str_cols].apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        df_sales = df_sales[mask]
        
    st.dataframe(df_sales, use_container_width=True, hide_index=True)
    
    # Calculate Total Sales Amount if numeric column exists
    numeric_cols = df_sales.select_dtypes(include=['number']).columns
    if len(numeric_cols) > 0:
        total_sum = df_sales[numeric_cols[-1]].sum()
        st.markdown(f"### 📌 Total Filtered Amount: PKR {total_sum:,.2f}")

# 3. Finished Goods & Inventory
elif app_mode == "📦 Finished Goods & Inventory":
    st.subheader("Products & Finished Goods Catalog")
    sheet_key = "Products" if "Products" in db else list(db.keys())[0]
    st.dataframe(db[sheet_key], use_container_width=True, hide_index=True)

# 4. Raw Materials Tracker
elif app_mode == "🧪 Raw Materials Tracker":
    st.subheader("Raw Materials Stock & Warehouse Ledger")
    sheet_key = "Raw_Materials" if "Raw_Materials" in db else list(db.keys())[0]
    st.dataframe(db[sheet_key], use_container_width=True, hide_index=True)

# 5. Customer Directory
elif app_mode == "👥 Customer Directory":
    st.subheader("Customer Accounts Directory")
    sheet_key = "Customers" if "Customers" in db else list(db.keys())[0]
    df_cust = db[sheet_key]
    
    search_cust = st.text_input("🔍 Search customer...")
    if search_cust:
        str_cols = df_cust.select_dtypes(include=['object']).columns
        mask = df_cust[str_cols].apply(lambda x: x.str.contains(search_cust, case=False, na=False)).any(axis=1)
        df_cust = df_cust[mask]
        
    st.dataframe(df_cust, use_container_width=True, hide_index=True)
    st.info(f"Total Accounts Listed: {len(df_cust)}")

# 6. Expenses & Owner Draws
elif app_mode == "💸 Expenses & Owner Draws":
    st.subheader("Operating Expenses & Owner Draws Log")
    tab1, tab2 = st.tabs(["Direct Operating Expenses", "Owner Draws"])
    
    with tab1:
        sheet_key = "Direct_Operating_Expenses" if "Direct_Operating_Expenses" in db else list(db.keys())[0]
        df_exp = db[sheet_key]
        st.dataframe(df_exp, use_container_width=True, hide_index=True)
        
        # Calculate sum for expenses
        numeric_exp = df_exp.select_dtypes(include=['number']).columns
        if len(numeric_exp) > 0:
            exp_total = df_exp[numeric_exp[-1]].sum()
            st.markdown(f"### 📌 Total Direct Operating Expenses: PKR {exp_total:,.2f}")
        
    with tab2:
        sheet_key = "Owners_Draws" if "Owners_Draws" in db else list(db.keys())[0]
        df_draws = db[sheet_key]
        st.dataframe(df_draws, use_container_width=True, hide_index=True)
        
        # Calculate sum for owner draws
        numeric_draws = df_draws.select_dtypes(include=['number']).columns
        if len(numeric_draws) > 0:
            draws_total = df_draws[numeric_draws[-1]].sum()
            st.markdown(f"### 📌 Total Owner Withdrawals: PKR {draws_total:,.2f}")
