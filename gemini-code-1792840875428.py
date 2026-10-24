import streamlit as st
import pandas as pd
import openpyxl
import plotly.express as px

# Page Configuration
st.set_page_config(
    page_title="ORCA Water Plant Management System",
    page_icon="💧",
    layout="wide"
)

# Custom Styling & Header
st.markdown("""
    <style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E293B; margin-bottom: 0px; }
    .sub-header { font-size: 1.1rem; color: #64748B; margin-bottom: 20px; }
    .metric-card { background-color: #F8FAFC; padding: 20px; border-radius: 10px; border: 1px solid #E2E8F0; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">💧 ORCA Water Plant Management System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Reconciled Master Financial & Operational Dashboard (FY 2026 - 2027)</div>', unsafe_allow_html=True)

# Load Definitive Excel Database
EXCEL_FILE = "ORCA_Water_Plant_Master_Database_Definitive_3.xlsx"

@st.cache_data
def load_data(file_path):
    try:
        xls = pd.ExcelFile(file_path)
        dashboard_pl = pd.read_excel(xls, "Dashboard_PL")
        sales_orders = pd.read_excel(xls, "Sales_Orders")
        products = pd.read_excel(xls, "Products")
        raw_materials = pd.read_excel(xls, "Raw_Materials")
        customers = pd.read_excel(xls, "Customers")
        expenses = pd.read_excel(xls, "Direct_Operating_Expenses")
        draws = pd.read_excel(xls, "Owners_Draws")
        unpaid = pd.read_excel(xls, "Unpaid_Invoices")
        return xls.sheet_names, sales_orders, products, raw_materials, customers, expenses, draws, unpaid
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        return None, None, None, None, None, None, None, None

sheets, sales_orders, products, raw_materials, customers, expenses, draws, unpaid = load_data(EXCEL_FILE)

if sales_orders is not None:
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

    if app_mode == "📊 Executive P&L Dashboard":
        st.subheader("Executive Financial Performance (P&L Summary)")
        
        # Top KPI Metric Cards
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
            pnl_data = {
                "P&L Category": [
                    "Total Gross Sales Revenue",
                    "Less: Total Discounts Allowed",
                    "Net Sales Revenue",
                    "Less: Cost of Goods Sold (COGS)",
                    "PRODUCT GROSS MARGIN",
                    "Less: Direct Plant Operating Expenses",
                    "GROSS PROFIT",
                    "Less: Indirect Expenses (Owner Draws)",
                    "NET PROFIT / CASH FLOW"
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

    elif app_mode == "🛍️ Sales Orders & Invoicing":
        st.subheader("Itemized Sales Orders & Invoicing Log")
        search_query = st.text_input("🔍 Search by Customer Name or Invoice No.")
        
        filtered_sales = sales_orders
        if search_query:
            filtered_sales = sales_orders[
                sales_orders['Client Name'].str.contains(search_query, case=False, na=False) | 
                sales_orders['Invoice No.'].str.contains(search_query, case=False, na=False)
            ]
        
        st.dataframe(filtered_sales, use_container_width=True, hide_index=True)

    elif app_mode == "📦 Finished Goods & Inventory":
        st.subheader("Finished Goods Catalog & Stock Valuation")
        st.dataframe(products, use_container_width=True, hide_index=True)

    elif app_mode == "🧪 Raw Materials Tracker":
        st.subheader("Raw Materials Warehouse & Consumption Tracker")
        st.dataframe(raw_materials, use_container_width=True, hide_index=True)

    elif app_mode == "👥 Customer Directory":
        st.subheader("Active Customer Directory (56 Accounts)")
        st.dataframe(customers, use_container_width=True, hide_index=True)

    elif app_mode == "💸 Expenses & Owner Draws":
        st.subheader("Direct Operating Expenses & Owner Withdrawals")
        tab1, tab2 = st.tabs(["Direct Operating Expenses", "Owner Draws"])
        with tab1:
            st.dataframe(expenses, use_container_width=True, hide_index=True)
        with tab2:
            st.dataframe(draws, use_container_width=True, hide_index=True)

else:
    st.warning("⚠️ Please ensure `ORCA_Water_Plant_Master_Database_Definitive_3.xlsx` is uploaded to your GitHub repository.")