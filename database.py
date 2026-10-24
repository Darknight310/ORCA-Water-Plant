import pandas as pd
import os
import streamlit as st

def load_database():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FILE_NAME = "ORCA_Water_Plant_Master_Database_Definitive.xlsx"
    FILE_PATH = os.path.join(BASE_DIR, FILE_NAME)
    if not os.path.exists(FILE_PATH):
        FILE_PATH = FILE_NAME

    xls = pd.ExcelFile(FILE_PATH)
    return {sheet: pd.read_excel(xls, sheet_name=sheet) for sheet in xls.sheet_names}

def init_session_state(raw_db):
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
