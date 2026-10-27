import pandas as pd
import streamlit as st

import db
import ui

ui.header("Reports", "Business reports — starting with sales by product")

section = ui.sections(["Sales By Products"], "report_tab")

if section == "Sales By Products":
    lines = db.get("invoice_lines", order="id")
    invoices = db.get("invoices", order="id")
    products = db.get("products", order="id")

    if lines.empty or invoices.empty or products.empty:
        st.info("No sales recorded yet.")
    else:
        h = lines.merge(invoices[["id", "invoice_date"]], left_on="invoice_id", right_on="id", suffixes=("", "_inv"))
        h = h.merge(products[["id", "name"]], left_on="product_id", right_on="id", suffixes=("", "_prod"))
        h["amount"] = h["qty"] * h["unit_rate"] - h["line_discount"]
        h["month_key"] = pd.to_datetime(h["invoice_date"]).dt.strftime("%Y-%m")
        h["Month"] = pd.to_datetime(h["month_key"] + "-01").dt.strftime("%b %Y")

        q = st.text_input("Search", placeholder="Search by product name or month, e.g. 'Aug' or '1500ml'", key="rep_search")
        qn = q.strip().lower()

        by_month = h.groupby(["month_key", "Month"]).agg(Quantity=("qty", "sum"), Amount=("amount", "sum")).reset_index()
        by_month = by_month.sort_values("month_key", ascending=False)
        by_prod = h.groupby(["month_key", "name"]).agg(Quantity=("qty", "sum"), Amount=("amount", "sum")).reset_index()

        shown_any = False
        for _, mrow in by_month.iterrows():
            mk, mlabel, mqty, mamt = mrow["month_key"], mrow["Month"], mrow["Quantity"], mrow["Amount"]
            prods = by_prod[by_prod["month_key"] == mk].sort_values("name")
            month_matches = (qn in mlabel.lower()) if qn else True

            if qn and not month_matches:
                prods = prods[prods["name"].str.lower().str.contains(qn)]
                if prods.empty:
                    continue

            shown_any = True
            label = mlabel + "   ·   Qty " + ui.money(mqty, 2) + "   ·   PKR " + ui.money(mamt, 2)
            with st.expander(label, expanded=bool(qn)):
                disp = prods.rename(columns={"name": "Product"})[["Product", "Quantity", "Amount"]]
                ui.table(ui.fmt(disp, ["Quantity", "Amount"], 2))

        if not shown_any:
            st.info("No results match your search.")

        st.markdown("---")
        t1, t2 = st.columns(2)
        t1.metric("Total Quantity (All Months)", ui.money(float(h["qty"].sum()), 2))
        t2.metric("Total Amount (All Months, PKR)", ui.money(float(h["amount"].sum()), 2))
        st.caption("Amounts shown here are before whole-invoice discounts, so the total may differ slightly "
                   "from 'Net Sales' on the Dashboard if you've applied invoice-level discounts.")
