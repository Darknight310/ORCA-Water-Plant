import streamlit as st
import pandas as pd
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
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">💧 ORCA Water Plant Management System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Reconciled Master Financial & Operational Dashboard (FY 2026 - 2027)</div>', unsafe_allow_html=True)

# Built-in Definitive Reconciled Data (No external file needed!)
@st.cache_data
def load_master_data():
    sales_orders = pd.DataFrame([
        {"Invoice No.": "INV-001", "Date": "2026-08-01", "Client Name": "Ali Malik", "Product": "500ml Bottle (12-pack)", "Qty": 20, "Total (PKR)": 9600.00, "Status": "Paid"},
        {"Invoice No.": "INV-002", "Date": "2026-08-03", "Client Name": "Usman Tariq", "Product": "1.5L Bottle (6-pack)", "Qty": 15, "Total (PKR)": 6750.00, "Status": "Paid"},
        {"Invoice No.": "INV-003", "Date": "2026-08-05", "Client Name": "Bilal Ahmed", "Product": "19L Dispenser Bottle", "Qty": 30, "Total (PKR)": 6000.00, "Status": "Paid"},
        {"Invoice No.": "INV-004", "Date": "2026-08-08", "Client Name": "Hassan Raza", "Product": "500ml Bottle (12-pack)", "Qty": 25, "Total (PKR)": 12000.00, "Status": "Paid"},
        {"Invoice No.": "INV-005", "Date": "2026-08-10", "Client Name": "Zainab Bibi", "Product": "1.5L Bottle (6-pack)", "Qty": 10, "Total (PKR)": 4500.00, "Status": "Paid"}
    ])
    
    products = pd.DataFrame([
        {"Product Name": "500ml Bottle (12-pack)", "Category": "Finished Goods", "Unit Price (PKR)": 480.00, "Stock Quantity": 140},
        {"Product Name": "1.5L Bottle (6-pack)", "Category": "Finished Goods", "Unit Price (PKR)": 450.00, "Stock Quantity": 95},
        {"Product Name": "19L Dispenser Bottle", "Category": "Finished Goods", "Unit Price (PKR)": 200.00, "Stock Quantity": 210}
    ])
    
    raw_materials = pd.DataFrame([
        {"Item Name": "Preforms (500ml)", "Unit": "Pieces", "Stock Level": 2500, "Cost per Unit (PKR)": 7.50},
        {"Item Name": "Caps (Blue)", "Unit": "Pieces", "Stock Level": 3100, "Cost per Unit (PKR)": 1.20},
        {"Item Name": "Labels (ORCA 500ml)", "Unit": "Pieces", "Stock Level": 4000, "Cost per Unit (PKR)": 0.80},
        {"Item Name": "Shrink Film", "Unit": "Rolls", "Stock Level": 14, "Cost per Unit (PKR)": 1200.00}
    ])
    
    customers = pd.DataFrame([
        {"Customer Name": "Ali Malik", "Area": "Narowal City", "Contact": "0300-1234567", "Account Balance (PKR)": 0.00, "Status": "Active"},
        {"Customer Name": "Usman Tariq", "Area": "Station Road", "Contact": "0301-9876543", "Account Balance (PKR)": 450.00, "Status": "Active"},
        {"Customer Name": "Bilal Ahmed", "Area": "Katchery Chowk", "Contact": "0302-5554433", "Account Balance (PKR)": 0.00, "Status": "Active"},
        {"Customer Name": "Hassan Raza", "Area": "Civil Lines", "Contact": "0303-3322110", "Account Balance (PKR)": 1200.00, "Status": "Active"}
    ])
    
    expenses = pd.DataFrame([
        {"Date": "2026-08-02", "Expense Category": "Electricity / Power", "Description": "Plant Generator & WAPDA", "Amount (PKR)": 6500.00},
        {"Date": "2026-08-12", "Expense Category": "Plant Maintenance", "Description": "RO Membrane Flushing & Carbon Filter Backwash", "Amount (PKR)": 3260.00},
        {"Date": "2026-08-20", "Expense Category": "Delivery Fuel", "Description": "Rickshaw Fuel for Deliveries", "Amount (PKR)": 2000.00}
    ])
    
    draws = pd.DataFrame([
        {"Date": "2026-08-15", "Owner Name": "Abu Bakar Siddique Butt", "Description": "Personal Profit Withdrawal", "Amount (PKR)": 10350.00},
        {"Date": "2026-08-28", "Owner Name": "Abu Bakar Siddique Butt", "Description": "Owner Draw for Personal Expense", "Amount (PKR)": 10000.00}
    ])
    
    return sales_orders, products, raw_materials, customers, expenses, draws

sales_orders, products, raw_materials, customers, expenses, draws = load_master_data()

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
    st.subheader("Active Customer Directory")
    st.dataframe(customers, use_container_width=True, hide_index=True)

elif app_mode == "💸 Expenses & Owner Draws":
    st.subheader("Direct Operating Expenses & Owner Withdrawals")
    tab1, tab2 = st.tabs(["Direct Operating Expenses", "Owner Draws"])
    with tab1:
        st.dataframe(expenses, use_container_width=True, hide_index=True)
    with tab2:
        st.dataframe(draws, use_container_width=True, hide_index=True)
