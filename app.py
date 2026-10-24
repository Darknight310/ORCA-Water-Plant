import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date

# Page Configuration
st.set_page_config(
    page_title="ORCA Water Plant Management System",
    page_icon="💧",
    layout="wide"
)

# Professional Custom UI & Styling (Modern Dashboard Look)
st.markdown("""
    <style>
    /* Main Theme & Background */
    .main { background-color: #F8FAFC; }
    
    /* Headers */
    .main-header { font-size: 2.4rem; font-weight: 800; color: #0F172A; margin-bottom: 0px; letter-spacing: -0.5px; }
    .sub-header { font-size: 1.1rem; color: #475569; margin-bottom: 25px; font-weight: 400; }
    
    /* Metric Cards Styling */
    div.stMetric {
        background-color: #FFFFFF;
        padding: 18px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border: 1px solid #E2E8F0;
    }
    div.stMetric label { color: #64748B !important; font-weight: 600 !important; font-size: 0.9rem !important; }
    div.stMetric [data-testid="stMetricValue"] { color: #0F172A !important; font-weight: 700 !important; font-size: 1.6rem !important; }
    
    /* Buttons */
    .stButton>button {
        background-color: #0284C7;
        color: white;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        padding: 0.5rem 1rem;
        box-shadow: 0 2px 4px rgba(2, 132, 199, 0.2);
    }
    .stButton>button:hover { background-color: #0369A1; color: white; }
    </style>
""", unsafe_allow_html=True)

# Header Section
st.markdown('<div class="main-header">💧 ORCA Water Plant Management System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Live Operational & Financial Control Center | Narowal Plant</div>', unsafe_allow_html=True)

# Database Loading with Session State Initialization
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_NAME = "ORCA_Water_Plant_Master_Database_Definitive_3.xlsx"
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
    st.error(f"⚠️ Error reading database file: {e}")
    st.stop()

# Initialize Session State so added entries persist while app is running
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

# Sidebar Navigation
st.sidebar.title("📌 Plant Navigation")
app_mode = st.sidebar.radio("Go to:", [
    "📊 Executive P&L Dashboard", 
    "🛍️ Sales Orders & Invoicing", 
    "📦 Finished Goods & Inventory", 
    "🧪 Raw Materials Tracker", 
    "👥 Customer Directory", 
    "💸 Expenses & Owner Draws"
])

# ==========================================
# 1. EXECUTIVE P&L DASHBOARD
# ==========================================
if app_mode == "📊 Executive P&L Dashboard":
    st.subheader("Executive Financial Performance (P&L Summary)")
    
    # Calculate live totals from session data if possible, or display baseline
    total_sales_revenue = 192320.00
    if not st.session_state.sales_df.empty:
        # Try to find a total amount column
        numeric_cols = st.session_state.sales_df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            calc_rev = st.session_state.sales_df[numeric_cols[-1]].sum()
            if calc_rev > 0:
                total_sales_revenue = calc_rev

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Gross Sales Revenue", value=f"PKR {total_sales_revenue:,.2f}")
    with col2:
        st.metric(label="Total Discounts Allowed", value="PKR 6,190.00")
    with col3:
        st.metric(label="Net Sales Revenue", value=f"PKR {total_sales_revenue - 6190:,.2f}")
    with col4:
        st.metric(label="Net Plant Cash Flow", value="PKR 17,966.46", delta="Profitable")

    st.markdown("---")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("### 📋 Reconciled P&L Statement")
        pnl_data = {
            "P&L Category": [
                "Total Gross Sales Revenue", "Less: Total Discounts Allowed", "Net Sales Revenue",
                "Less: Cost of Goods Sold (COGS)", "PRODUCT GROSS MARGIN", "Less: Direct Plant Operating Expenses",
                "GROSS PROFIT", "Less: Indirect Expenses (Owner Draws)", "NET PROFIT / CASH FLOW"
            ],
            "Amount (PKR)": [
                f"{total_sales_revenue:,.2f}", "-6,190.00", f"{total_sales_revenue - 6190:,.2f}", 
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
        fig = px.pie(chart_data, values="Amount", names="Category", title="Financial Allocation Breakdown", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 2. SALES ORDERS & INVOICING (Interactive Entry)
# ==========================================
elif app_mode == "🛍️ Sales Orders & Invoicing":
    st.subheader("🛍️ Sales Orders & Invoicing Management")
    
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
                st.success(f"Successfully recorded order {inv_no} for {client_name}!")
                st.rerun()

    search_query = st.text_input("🔍 Search Sales Records (Client Name or Invoice No.):")
    df_sales = st.session_state.sales_df
    if search_query:
        str_cols = df_sales.select_dtypes(include=['object']).columns
        mask = df_sales[str_cols].apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        df_sales = df_sales[mask]
        
    st.dataframe(df_sales, use_container_width=True, hide_index=True)
    
    numeric_cols = df_sales.select_dtypes(include=['number']).columns
    if len(numeric_cols) > 0:
        total_sum = df_sales[numeric_cols[-1]].sum()
        st.markdown(f"### 📌 Total Filtered Sales Amount: PKR {total_sum:,.2f}")

# ==========================================
# 3. FINISHED GOODS & INVENTORY
# ==========================================
elif app_mode == "📦 Finished Goods & Inventory":
    st.subheader("📦 Finished Goods Catalog & Stock Valuation")
    st.dataframe(st.session_state.products_df, use_container_width=True, hide_index=True)

# ==========================================
# 4. RAW MATERIALS TRACKER
# ==========================================
elif app_mode == "🧪 Raw Materials Tracker":
    st.subheader("🧪 Raw Materials Warehouse & Stock Ledger")
    st.dataframe(st.session_state.raw_materials_df, use_container_width=True, hide_index=True)

# ==========================================
# 5. CUSTOMER DIRECTORY (Interactive Entry)
# ==========================================
elif app_mode == "👥 Customer Directory":
    st.subheader("👥 Active Customer Accounts Directory")
    
    with st.expander("➕ Add New Customer Account", expanded=False):
        with st.form("new_customer_form"):
            col1, col2 = st.columns(2)
            with col1:
                c_name = st.text_input("Customer / Store Name")
                c_route = st.text_input("Route / Area (e.g., Narowal City)")
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
                st.success(f"Customer {c_name} added successfully!")
                st.rerun()

    search_cust = st.text_input("🔍 Search Customer Name or Route:")
    df_cust = st.session_state.customers_df
    if search_cust:
        str_cols = df_cust.select_dtypes(include=['object']).columns
        mask = df_cust[str_cols].apply(lambda x: x.str.contains(search_cust, case=False, na=False)).any(axis=1)
        df_cust = df_cust[mask]
        
    st.dataframe(df_cust, use_container_width=True, hide_index=True)
    st.info(f"Total Active Accounts: {len(df_cust)}")

# ==========================================
# 6. EXPENSES & OWNER DRAWS (Interactive Entry)
# ==========================================
elif app_mode == "💸 Expenses & Owner Draws":
    st.subheader("💸 Operating Expenses & Owner Withdrawals")
    
    with st.expander("➕ Record New Expense or Owner Draw", expanded=False):
        tab_e1, tab_e2 = st.tabs(["Log Operating Expense", "Log Owner Draw"])
        with tab_e1:
            with st.form("exp_form"):
                e_date = st.date_input("Expense Date", value=date.today())
                e_cat = st.selectbox("Category", ["Electricity & Power", "Plant Maintenance", "Delivery & Transport", "Miscellaneous"])
                e_desc = st.text_input("Description (e.g., Generator Diesel)")
                e_amt = st.number_input("Amount (PKR)", min_value=0.0, value=1000.0)
                sub_e = st.form_submit_button("Save Expense")
                if sub_e:
                    new_e = {
                        "Expense ID": f"EXP-{len(st.session_state.expenses_df)+1:02d}",
                        "Date": str(e_date),
                        "Category": e_cat,
                        "Description": e_desc,
                        "Amount (PKR)": e_amt
                    }
                    st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_e])], ignore_index=True)
                    st.success("Expense logged successfully!")
                    st.rerun()
        with tab_e2:
            with st.form("draw_form"):
                d_date = st.date_input("Withdrawal Date", value=date.today(), key="d_date")
                d_owner = st.text_input("Owner Name", value="Abu Bakar Siddique Butt")
                d_desc = st.text_input("Description", value="Personal Profit Withdrawal")
                d_amt = st.number_input("Withdrawal Amount (PKR)", min_value=0.0, value=5000.0, key="d_amt")
                sub_d = st.form_submit_button("Save Owner Draw")
                if sub_d:
                    new_d = {
                        "Draw ID": f"DRW-{len(st.session_state.draws_df)+1:02d}",
                        "Date": str(d_date),
                        "Owner Name": d_owner,
                        "Description": d_desc,
                        "Amount (PKR)": d_amt
                    }
                    st.session_state.draws_df = pd.concat([st.session_state.draws_df, pd.DataFrame([new_d])], ignore_index=True)
                    st.success("Owner draw logged successfully!")
                    st.rerun()

    tab1, tab2 = st.tabs(["Direct Operating Expenses", "Owner Draws"])
    
    with tab1:
        df_exp = st.session_state.expenses_df
        st.dataframe(df_exp, use_container_width=True, hide_index=True)
        numeric_exp = df_exp.select_dtypes(include=['number']).columns
        if len(numeric_exp) > 0:
            exp_total = df_exp[numeric_exp[-1]].sum()
            st.markdown(f"### 📌 Total Operating Expenses: PKR {exp_total:,.2f}")
        
    with tab2:
        df_draws = st.session_state.draws_df
        st.dataframe(df_draws, use_container_width=True, hide_index=True)
        numeric_draws = df_draws.select_dtypes(include=['number']).columns
        if len(numeric_draws) > 0:
            draws_total = df_draws[numeric_draws[-1]].sum()
            st.markdown(f"### 📌 Total Owner Withdrawals: PKR {draws_total:,.2f}")
