import pandas as pd
import streamlit as st

@st.cache_data
def load_database():
    excel_path = "ORCA_Water_Plant_Master_Database_Definitive.xlsx"
    xls = pd.ExcelFile(excel_path)
    
    # Load sheets
    sales_df = pd.read_excel(xls, sheet_name="Sales Orders")
    
    # Clean up sales_df to filter out rogue summary/total rows (like INV#93)
    if "Invoice No." in sales_df.columns:
        sales_df = sales_df[~sales_df["Invoice No."].astype(str).str.contains("Total|Sum|INV#93", case=False, na=False)]
        
    customers_df = pd.read_excel(xls, sheet_name="Customers")
    products_df = pd.read_excel(xls, sheet_name="Products")
    raw_materials_df = pd.read_excel(xls, sheet_name="Raw Materials")
    expenses_df = pd.read_excel(xls, sheet_name="Expenses")
    draws_df = pd.read_excel(xls, sheet_name="Owner Draws")
    
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
