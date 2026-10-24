import streamlit as st
import pandas as pd
import io
from datetime import date

def render_sales_form():
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

def render_customer_form():
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

def convert_pnl_to_excel():
    pnl_export_data = {
        "Financial Category": [
            "Gross Sales Revenue", "Less: Total Discounts Allowed", "Net Sales Revenue",
            "Less: Cost of Goods Sold (COGS)", "Gross Profit", "Less: Direct Operating Expenses",
            "Operating Net Profit", "Less: Owner Personal Draws", "Net Retained Cash Flow"
        ],
        "Amount (PKR)": [
            192320.00, -6190.00, 186130.00, 
            -136053.54, 50076.46, -11760.00, 
            38316.46, -20350.00, 17966.46
        ],
        "% of Revenue": [
            "103.3%", "-3.3%", "100.0%", "-73.1%", "26.9%", "-6.3%", "20.6%", "-10.9%", "9.7%"
        ]
    }
    df = pd.DataFrame(pnl_export_data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Master_PnL')
    processed_data = output.getvalue()
    return processed_data
