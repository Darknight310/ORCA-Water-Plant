import pandas as pd
import streamlit as st

@st.cache_data
def load_database():
    excel_path = "ORCA_Water_Plant_Master_Database_Definitive.xlsx"
    xls = pd.ExcelFile(excel_path)
    sheet_names = xls.sheet_names
    
    # Helper function to find the right sheet name dynamically
    def get_matching_sheet(possible_names):
        for name in possible_names:
            for sheet in sheet_names:
                if name.lower() in sheet.lower():
                    return sheet
        return sheet_names[0] # Fallback to first sheet if none match

    # Load sheets safely based on partial name matching
    sales_sheet = get_matching_sheet(["Sales", "Order", "Invoices"])
    customers_sheet = get_matching_sheet(["Customer", "Client"])
    products_sheet = get_matching_sheet(["Product", "Inventory", "Finished"])
    raw_sheet = get_matching_sheet(["Raw", "Material", "Stock"])
    expenses_sheet = get_matching_sheet(["Expense", "Cost"])
    draws_sheet = get_matching_sheet(["Draw", "Owner", "Withdrawal"])

    sales_df = pd.read_excel(xls, sheet_name=sales_sheet)
    
    # Clean up sales_df to filter out rogue summary/total rows (like INV#93)
    if not sales_df.empty:
        first_col = sales_df.columns[0]
        sales_df = sales_df[~sales_df[first_col].astype(str).str.contains("Total|Sum|INV#93", case=False, na=False)]

    customers_df = pd.read_excel(xls, sheet_name=customers_sheet)
    products_df = pd.read_excel(xls, sheet_name=products_sheet)
    raw_materials_df = pd.read_excel(xls, sheet_name=raw_sheet)
    expenses_df = pd.read_excel(xls, sheet_name=expenses_sheet)
    draws_df = pd.read_excel(xls, sheet_name=draws_sheet)
    
    return {
        "sales": sales_df,
        "customers": customers_df,
        "products": products_df,
        "raw_materials": raw_materials_df,
        "expenses": expenses_df,
        "draws": draws_df
    }

def init_session_state(raw_db):
    if "sales_df" not in st.session_state:
        st.session_state.sales_df = raw_db["sales"]
    if "customers_df" not in st.session_state:
        st.session_state.customers_df = raw_db["customers"]
    if "products_df" not in st.session_state:
        st.session_state.products_df = raw_db["products"]
    if "raw_materials_df" not in st.session_state:
        st.session_state.raw_materials_df = raw_db["raw_materials"]
    if "expenses_df" not in st.session_state:
        st.session_state.expenses_df = raw_db["expenses"]
    if "draws_df" not in st.session_state:
        st.session_state.draws_df = raw_db["draws"]
