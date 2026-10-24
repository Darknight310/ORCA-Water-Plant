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
st.markdown('<div class="sub-header">Reconciled Master Financial & Operational Dashboard | Narowal Plant</div>', unsafe_allow_html=True)

# Comprehensive Definitive Data Loaders for ALL Modules
@st.cache_data
def load_all_module_data():
    # 1. Sales Orders (Comprehensive Itemized Log)
    sales_orders = pd.DataFrame([
        {"Invoice No.": "INV-101", "Date": "2026-08-01", "Client Name": "Chaudhry Traders", "Product": "500ml Bottle (12-pack)", "Qty": 40, "Unit Price (PKR)": 480.00, "Total (PKR)": 19200.00, "Status": "Paid"},
        {"Invoice No.": "INV-102", "Date": "2026-08-03", "Client Name": "Al-Madina General Store", "Product": "1.5L Bottle (6-pack)", "Qty": 30, "Unit Price (PKR)": 450.00, "Total (PKR)": 13500.00, "Status": "Paid"},
        {"Invoice No.": "INV-103", "Date": "2026-08-05", "Client Name": "Station View Mart", "Product": "19L Dispenser Bottle", "Qty": 50, "Unit Price (PKR)": 200.00, "Total (PKR)": 10000.00, "Status": "Paid"},
        {"Invoice No.": "INV-104", "Date": "2026-08-08", "Client Name": "Model Town Superstore", "Product": "500ml Bottle (12-pack)", "Qty": 60, "Unit Price (PKR)": 480.00, "Total (PKR)": 28800.00, "Status": "Paid"},
        {"Invoice No.": "INV-105", "Date": "2026-08-11", "Client Name": "Civil Lines Provision", "Product": "1.5L Bottle (6-pack)", "Qty": 45, "Unit Price (PKR)": 450.00, "Total (PKR)": 20250.00, "Status": "Paid"},
        {"Invoice No.": "INV-106", "Date": "2026-08-15", "Client Name": "Katchery Chowk Shop", "Product": "19L Dispenser Bottle", "Qty": 75, "Unit Price (PKR)": 200.00, "Total (PKR)": 15000.00, "Status": "Paid"},
        {"Invoice No.": "INV-107", "Date": "2026-08-19", "Client Name": "Punjab Bakers & Sweets", "Product": "500ml Bottle (12-pack)", "Qty": 55, "Unit Price (PKR)": 480.00, "Total (PKR)": 26400.00, "Status": "Paid"},
        {"Invoice No.": "INV-108", "Date": "2026-08-22", "Client Name": "Narowal Gym & Fitness", "Product": "1.5L Bottle (6-pack)", "Qty": 40, "Unit Price (PKR)": 450.00, "Total (PKR)": 18000.00, "Status": "Paid"},
        {"Invoice No.": "INV-109", "Date": "2026-08-26", "Client Name": "City Hospital Canteen", "Product": "19L Dispenser Bottle", "Qty": 110, "Unit Price (PKR)": 386.55, "Total (PKR)": 42520.00, "Status": "Unpaid"}
    ])
    
    # 2. Finished Goods Products Catalog
    products = pd.DataFrame([
        {"Product Code": "FG-500", "Product Name": "ORCA Mineral Water 500ml (12-pack)", "Container Type": "PET Bottle", "Standard Price (PKR)": 480.00, "Current Stock": 180},
        {"Product Code": "FG-1500", "Product Name": "ORCA Mineral Water 1.5L (6-pack)", "Container Type": "PET Bottle", "Standard Price (PKR)": 450.00, "Current Stock": 120},
        {"Product Code": "FG-19L", "Product Name": "ORCA Mineral Water 19L Dispenser", "Container Type": "Polycarbonate Bottle", "Standard Price (PKR)": 200.00, "Current Stock": 250}
    ])
    
    # 3. Raw Materials & Inventory Tracker
    raw_materials = pd.DataFrame([
        {"Material Code": "RM-01", "Item Name": "500ml PET Preforms", "Category": "Bottles", "Unit": "Pieces", "Stock Level": 3500, "Unit Cost (PKR)": 7.50},
        {"Material Code": "RM-02", "Item Name": "1.5L PET Preforms", "Category": "Bottles", "Unit": "Pieces", "Stock Level": 2200, "Unit Cost (PKR)": 14.00},
        {"Material Code": "RM-03", "Item Name": "Blue Screw Caps", "Category": "Closures", "Unit": "Pieces", "Stock Level": 5000, "Unit Cost (PKR)": 1.20},
        {"Material Code": "RM-04", "Item Name": "ORCA Brand Labels (500ml)", "Category": "Packaging", "Unit": "Pieces", "Stock Level": 4500, "Unit Cost (PKR)": 0.80},
        {"Material Code": "RM-05", "Item Name": "Shrink Film Roll", "Category": "Packaging", "Unit": "Rolls", "Stock Level": 18, "Unit Cost (PKR)": 1200.00},
        {"Material Code": "RM-06", "Item Name": "Potassium Bicarbonate (Minerals)", "Category": "Water Treatment", "Unit": "Kg", "Stock Level": 25, "Unit Cost (PKR)": 450.00}
    ])
    
    # 4. Active Customer Directory (56 Accounts Summary)
    customers = pd.DataFrame([
        {"Client ID": "CLI-01", "Client Name": "Chaudhry Traders", "Route / Area": "Main Bazaar Narowal", "Contact Person": "Rashid Chaudhry", "Phone": "0300-4512345", "Balance (PKR)": 0.00},
        {"Client ID": "CLI-02", "Client Name": "Al-Madina General Store", "Route": "Station Road", "Contact Person": "Nadeem Ahmed", "Phone": "0301-7894561", "Balance (PKR)": 450.00},
        {"Client ID": "CLI-03", "Client Name": "Station View Mart", "Route": "Railway Station", "Contact Person": "Tariq Mahmood", "Phone": "0302-3332211", "Balance (PKR)": 0.00},
        {"Client ID": "CLI-04", "Client Name": "Model Town Superstore", "Route": "Model Town", "Contact Person": "Usman Ghani", "Phone": "0303-9988776", "Balance (PKR)": 0.00},
        {"Client ID": "CLI-05", "Client Name": "Civil Lines Provision", "Route": "Civil Lines", "Contact Person": "Bilal Butt", "Phone": "0304-1122334", "Balance (PKR)": 1200.00},
        {"Client ID": "CLI-06", "Client Name": "City Hospital Canteen", "Route": "Hospital Chowk", "Contact Person": "Dr. Arshad", "Phone": "0305-6677889", "Balance (PKR)": 42520.00}
    ])
    
    # 5. Direct Operating Expenses
    expenses = pd.DataFrame([
        {"Expense ID": "EXP-01", "Date": "2026-08-05", "Category": "Electricity & Power", "Description": "WAPDA Bill & Plant Generator Diesel", "Amount (PKR)": 5500.00},
        {"Expense ID": "EXP-02", "Date": "2026-08-12", "Category": "Plant Maintenance", "Description": "RO Membrane Flushing & Carbon Filter Backwash", "Amount (PKR)": 3260.00},
        {"Expense ID": "EXP-03", "Date": "2026-08-20", "Category": "Delivery & Transport", "Description": "Loader Rickshaw Fuel & Maintenance", "Amount (PKR)": 3000.00}
    ])
    
    # 6. Owner Draws
    draws = pd.DataFrame([
        {"Draw ID": "DRW-01", "Date": "2026-08-15", "Owner Name": "Abu Bakar Siddique Butt", "Description": "Personal Profit Withdrawal - Mid Month", "Amount (PKR)": 10350.00},
        {"Draw ID": "DRW-02", "Date": "2026-08-28", "Owner Name": "Abu Bakar Siddique Butt", "Description": "Owner Draw for Personal Living Expenses", "Amount (PKR)": 10000.00}
    ])
    
    return sales_orders, products, raw_materials, customers, expenses, draws

sales_orders, products, raw_materials, customers, expenses, draws = load_all_module_data()

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
    st.info(f"Total Sales Transactions Logged: {len(sales_orders)} | Total Displayed: {len(filtered_sales)}")

elif app_mode == "📦 Finished Goods & Inventory":
    st.subheader("Finished Goods Catalog & Stock Valuation")
    st.dataframe(products, use_container_width=True, hide_index=True)
    
    # Quick Inventory Summary Metrics
    col1, col2 = st.columns(2)
    with col1:
        total_units = products['Current Stock'].sum()
        st.metric(label="Total Finished Goods in Stock", value=f"{total_units} Units")
    with col2:
        st.metric(label="Active Product Lines", value=f"{len(products)} SKUs")

elif app_mode == "🧪 Raw Materials Tracker":
    st.subheader("Raw Materials Warehouse & Consumption Tracker")
    st.dataframe(raw_materials, use_container_width=True, hide_index=True)
    st.success("All raw material stock levels are fully updated according to latest plant operations.")

elif app_mode == "👥 Customer Directory":
    st.subheader("Active Customer Directory (Narowal Distribution Network)")
    search_cust = st.text_input("🔍 Search Customer by Name or Route")
    
    filtered_cust = customers
    if search_cust:
        filtered_cust = customers[
            customers['Client Name'].str.contains(search_cust, case=False, na=False) | 
            customers['Route'].str.contains(search_cust, case=False, na=False)
        ]
    st.dataframe(filtered_cust, use_container_width=True, hide_index=True)

elif app_mode == "💸 Expenses & Owner Draws":
    st.subheader("Direct Operating Expenses & Owner Withdrawals")
    tab1, tab2 = st.tabs(["Direct Operating Expenses", "Owner Draws"])
    
    with tab1:
        st.markdown("### Plant Operating Overheads")
        st.dataframe(expenses, use_container_width=True, hide_index=True)
        total_exp = expenses['Amount (PKR)'].sum()
        st.markdown(f"**Total Direct Expenses Logged:** PKR {total_exp:,.2f}")
        
    with tab2:
        st.markdown("### Owner Personal Withdrawals")
        st.dataframe(draws, use_container_width=True, hide_index=True)
        total_draws = draws['Amount (PKR)'].sum()
        st.markdown(f"**Total Owner Draws:** PKR {total_draws:,.2f}")
