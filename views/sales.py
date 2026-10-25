import datetime as dt

import pandas as pd
import streamlit as st

import db
import ui

ui.header("Sales & Invoices", "Create invoices, see what customers owe, record payments")

customers = db.get("customers", order="name")
products = db.get("products", order="id")
summ = db.get("v_invoice_summary", order="id")
fg = db.get("v_product_stock", order="id")

if customers.empty or products.empty:
    st.error("Add customers and products first.")
    st.stop()

cust_names = customers["name"].tolist()
prod_names = products["name"].tolist()

tab_new, tab_inv, tab_pay = st.tabs(["New invoice", "Invoices", "Payments"])

# ---------------------------------------------------------------- new invoice
with tab_new:
    n = st.session_state.setdefault("inv_n", 0)
    existing = summ["invoice_no"].tolist() if not summ.empty else []
    c1, c2, c3 = st.columns([1, 1, 2])
    inv_no = c1.text_input("Invoice no.", value=db.next_no(existing, "INV#"), key="inv_no_" + str(n))
    inv_date = c2.date_input("Date", value=dt.date.today(), key="inv_date_" + str(n))
    cust = c3.selectbox("Customer", cust_names, index=None, placeholder="Choose a customer",
                        key="inv_cust_" + str(n))

    st.markdown("**Items**  ·  click the empty row, pick a product, type bundles and rate")
    if not fg.empty and fg["sold"].sum() > 0:
        rates = ", ".join(r["name"] + ": " + ui.money(r["avg_rate"]) for _, r in fg.iterrows() if r["avg_rate"] > 0)
        st.caption("Your average selling rates so far, per bundle  →  " + rates)
    base = pd.DataFrame([{"Product": None, "Bundles": None, "Rate (PKR)": None, "Discount (PKR)": 0.0}])
    lines = st.data_editor(
        base, num_rows="dynamic", key="inv_lines_" + str(n),
        column_config={
            "Product": st.column_config.SelectboxColumn("Product", options=prod_names, required=True),
            "Bundles": st.column_config.NumberColumn("Bundles", min_value=0, step=1),
            "Rate (PKR)": st.column_config.NumberColumn("Rate (PKR)", min_value=0, format="%.2f"),
            "Discount (PKR)": st.column_config.NumberColumn("Line discount (PKR)", min_value=0, format="%.2f"),
        },
    )
    valid = lines.dropna(subset=["Product", "Bundles", "Rate (PKR)"]).copy()
    valid = valid[valid["Bundles"] > 0]
    valid["Discount (PKR)"] = valid["Discount (PKR)"].fillna(0)
    gross = float((valid["Bundles"] * valid["Rate (PKR)"]).sum())
    line_disc = float(valid["Discount (PKR)"].sum())

    d1, d2, d3 = st.columns(3)
    inv_disc = d1.number_input("Discount on the whole invoice (PKR)", min_value=0.0, step=10.0,
                               key="inv_disc_" + str(n))
    received = d2.number_input("Payment received now (PKR)", min_value=0.0, step=100.0,
                               key="inv_rec_" + str(n))
    method = d3.selectbox("Payment method", db.METHODS, key="inv_meth_" + str(n))
    net = gross - line_disc - float(inv_disc)

    m1, m2, m3 = st.columns(3)
    m1.metric("Gross", "PKR " + ui.money(gross))
    m2.metric("Discounts", "PKR " + ui.money(line_disc + float(inv_disc)))
    m3.metric("Invoice total", "PKR " + ui.money(net))

    if st.button("Save invoice", type="primary", key="inv_save_" + str(n)):
        no = inv_no.strip()
        if not cust:
            st.error("Choose a customer.")
        elif not no:
            st.error("Enter an invoice number.")
        elif no in existing:
            st.error("Invoice " + no + " already exists. Use a different number.")
        elif valid.empty:
            st.error("Add at least one item with product, bundles and rate.")
        elif net <= 0:
            st.error("The invoice total must be more than zero.")
        elif float(received) > net + 0.01:
            st.error("Payment received cannot be more than the invoice total.")
        else:
            try:
                cust_id = int(customers.loc[customers["name"] == cust, "id"].iloc[0])
                pid = dict(zip(products["name"], products["id"]))
                res = db.insert("invoices", {"invoice_no": no, "invoice_date": inv_date.isoformat(),
                                             "customer_id": cust_id, "invoice_discount": float(inv_disc)})
                inv_id = int(res[0]["id"])
                try:
                    db.insert("invoice_lines", [
                        {"invoice_id": inv_id, "product_id": int(pid[r["Product"]]),
                         "qty": float(r["Bundles"]), "unit_rate": float(r["Rate (PKR)"]),
                         "line_discount": float(r["Discount (PKR)"])}
                        for _, r in valid.iterrows()])
                except Exception:
                    db.delete("invoices", inv_id)
                    raise
                if float(received) > 0:
                    db.insert("payments", {"payment_date": inv_date.isoformat(), "invoice_id": inv_id,
                                           "customer_id": cust_id, "amount": float(received), "method": method})
                st.session_state["inv_n"] = n + 1
                st.session_state["flash"] = "Invoice " + no + " saved (PKR " + ui.money(net) + ")."
                st.rerun()
            except Exception as e:
                st.error("Could not save the invoice: " + str(e))

# -------------------------------------------------------------------- invoices
with tab_inv:
    if summ.empty:
        st.info("No invoices yet.")
    else:
        owed = float(summ.loc[summ["balance_due"] > 0, "balance_due"].sum())
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Invoices", str(len(summ)))
        k2.metric("Billed", "PKR " + ui.money(summ["net_amount"].sum()))
        k3.metric("Received", "PKR " + ui.money(summ["received"].sum()))
        k4.metric("Outstanding", "PKR " + ui.money(owed))
        f1, f2 = st.columns([2, 1])
        q = f1.text_input("Search", placeholder="Invoice number or customer", key="inv_search")
        stat = f2.multiselect("Status", ["Unpaid", "Partial", "Paid"], default=["Unpaid", "Partial", "Paid"],
                              key="inv_status")
        v = summ[summ["status"].isin(stat)]
        if q:
            mask = (v["invoice_no"].str.contains(q, case=False, na=False) |
                    v["customer_name"].str.contains(q, case=False, na=False))
            v = v[mask]
        v = v.sort_values("id", ascending=False)
        show = v[["invoice_no", "invoice_date", "customer_name", "net_amount", "received", "balance_due", "status"]]
        show = ui.fmt(show, ["net_amount", "received", "balance_due"])
        show.columns = ["Invoice", "Date", "Customer", "Amount", "Received", "Balance due", "Status"]
        ui.table(show)

        with st.expander("See the items on an invoice"):
            pick = st.selectbox("Invoice", v["invoice_no"].tolist(), index=None,
                                placeholder="Choose an invoice", key="inv_detail")
            if pick:
                row = summ[summ["invoice_no"] == pick].iloc[0]
                il = db.get("invoice_lines", order="id")
                il = il[il["invoice_id"] == row["id"]].copy()
                il["Product"] = il["product_id"].map(db.name_map(products))
                il["Amount"] = il["qty"] * il["unit_rate"] - il["line_discount"]
                det = il[["Product", "qty", "unit_rate", "line_discount", "Amount"]]
                det.columns = ["Product", "Bundles", "Rate", "Line discount", "Amount"]
                ui.table(ui.fmt(det, ["Bundles", "Rate", "Line discount", "Amount"], 2))
                if row["invoice_discount"] > 0:
                    st.caption("Discount on whole invoice: PKR " + ui.money(row["invoice_discount"]))

# -------------------------------------------------------------------- payments
with tab_pay:
    open_inv = summ[summ["balance_due"] > 0].sort_values("id", ascending=False) if not summ.empty else summ
    if open_inv.empty:
        st.success("All invoices are fully paid.")
    else:
        labels = {}
        for _, r in open_inv.iterrows():
            labels[r["invoice_no"] + "  ·  " + r["customer_name"] + "  ·  due " + ui.money(r["balance_due"])] = r
        pick = st.selectbox("Invoice being paid", list(labels.keys()), index=None,
                            placeholder="Choose an unpaid invoice", key="pay_inv")
        if pick:
            r = labels[pick]
            due = float(r["balance_due"])
            p1, p2, p3 = st.columns(3)
            amt = p1.number_input("Amount received (PKR)", min_value=0.0, value=due, step=100.0,
                                  key="pay_amt_" + str(int(r["id"])))
            pdate = p2.date_input("Date", value=dt.date.today(), key="pay_date")
            pmeth = p3.selectbox("Method", db.METHODS, key="pay_meth")
            pnotes = st.text_input("Notes (optional)", key="pay_notes")
            if st.button("Record payment", type="primary", key="pay_save"):
                if amt <= 0:
                    st.error("Enter an amount.")
                elif amt > due + 0.01:
                    st.error("That is more than the balance due (PKR " + ui.money(due) + ").")
                else:
                    try:
                        db.insert("payments", {"payment_date": pdate.isoformat(), "invoice_id": int(r["id"]),
                                               "customer_id": int(r["customer_id"]), "amount": float(amt),
                                               "method": pmeth, "notes": pnotes or None})
                        st.session_state["flash"] = "Payment of PKR " + ui.money(amt) + " recorded for " + r["invoice_no"] + "."
                        st.rerun()
                    except Exception as e:
                        st.error("Could not save the payment: " + str(e))

    pay = db.get("payments", order="id", desc=True)
    st.markdown("#### Payment history")
    if pay.empty:
        st.info("No payments recorded yet.")
    else:
        inv_name = db.name_map(summ, "invoice_no")
        cust_map = db.name_map(customers)
        h = pay.copy()
        h["Invoice"] = h["invoice_id"].map(inv_name)
        h["Customer"] = h["customer_id"].map(cust_map)
        h = h.head(200)
        show = h[["payment_date", "Invoice", "Customer", "amount", "method", "notes"]]
        show = ui.fmt(show, ["amount"])
        show.columns = ["Date", "Invoice", "Customer", "Amount", "Method", "Notes"]
        ui.table(show)
        ui.delete_entry("payments", h, lambda r: str(r["Invoice"]) + " · " + str(r["Customer"]) + " · " + ui.money(r["amount"]), "pay")
