import datetime as dt

import pandas as pd
import streamlit as st

import db
import ui

ui.header("Sales & Invoices", "Invoices, sale orders, payments and receivables")

customers = db.get("customers", order="name")
products = db.get("products", order="id")
summ = db.get("v_invoice_summary", order="id")
fg = db.get("v_product_stock", order="id")
try:
    orders = db.get("v_sale_order_summary", order="id")
except Exception:
    orders = None

if customers.empty or products.empty:
    st.error("Add customers and products first.")
    st.stop()

cust_names = customers["name"].tolist()
prod_names = products["name"].tolist()
pname = db.name_map(products)
pid_by_name = dict(zip(products["name"], products["id"]))
cid_by_name = dict(zip(customers["name"], customers["id"]))

LINE_COLS = ["Product", "Bundles", "Rate (PKR)", "Discount (PKR)"]


def blank_lines():
    return pd.DataFrame([{"Product": None, "Bundles": None, "Rate (PKR)": None, "Discount (PKR)": 0.0}])


def editor(key, base):
    return st.data_editor(
        base, num_rows="dynamic", key=key,
        column_config={
            "Product": st.column_config.SelectboxColumn("Product", options=prod_names, required=True),
            "Bundles": st.column_config.NumberColumn("Bundles", min_value=0, step=1),
            "Rate (PKR)": st.column_config.NumberColumn("Rate (PKR)", min_value=0, format="%.2f"),
            "Discount (PKR)": st.column_config.NumberColumn("Line Discount (PKR)", min_value=0, format="%.2f"),
        })


def clean(lines):
    v = lines.dropna(subset=["Product", "Bundles", "Rate (PKR)"]).copy()
    v = v[v["Bundles"] > 0]
    v["Discount (PKR)"] = v["Discount (PKR)"].fillna(0)
    return v


def line_rows(df, fk, fk_value):
    return [{fk: fk_value, "product_id": int(pid_by_name[r["Product"]]), "qty": float(r["Bundles"]),
             "unit_rate": float(r["Rate (PKR)"]), "line_discount": float(r["Discount (PKR)"])}
            for _, r in df.iterrows()]


def lines_frame(lines_df):
    return pd.DataFrame({
        "Product": lines_df["product_id"].map(pname).values,
        "Bundles": lines_df["qty"].astype(float).values,
        "Rate (PKR)": lines_df["unit_rate"].astype(float).values,
        "Discount (PKR)": lines_df["line_discount"].astype(float).values}).reset_index(drop=True)


section = ui.sections(["New Invoice", "Invoices", "Sale Orders", "Payments"], "sales_tab")

# ============================================================== NEW INVOICE
if section == "New Invoice":
    pre = st.session_state.get("inv_pre")
    n = st.session_state.setdefault("inv_n", 0)
    mode = pre["mode"] if pre else "new"
    existing = summ["invoice_no"].tolist() if not summ.empty else []

    if pre:
        text = ("Editing invoice " + pre["invoice_no"]) if mode == "edit" else \
               ("Converting sale order " + pre["order_no"] + " into an invoice")
        i1, i2 = st.columns([5, 1])
        i1.info(text)
        if i2.button("Cancel", key="inv_cancel_" + str(n)):
            st.session_state.pop("inv_pre", None)
            st.session_state["inv_n"] = n + 1
            st.rerun()

    default_no = pre["invoice_no"] if mode == "edit" else db.next_no(existing, "INV#")
    c1, c2, c3 = st.columns([1, 1, 2])
    inv_no = c1.text_input("Invoice No.", value=default_no, key="inv_no_" + str(n))
    inv_date = c2.date_input("Date", value=pre["date"] if mode == "edit" else dt.date.today(), key="inv_date_" + str(n))
    cidx = cust_names.index(pre["customer"]) if pre and pre["customer"] in cust_names else None
    cust = c3.selectbox("Customer", cust_names, index=cidx, placeholder="Choose A Customer", key="inv_cust_" + str(n))

    st.markdown("**Items**  ·  click the empty row, pick a product, type bundles and rate")
    if not fg.empty and fg["sold"].sum() > 0:
        rates = ", ".join(r["name"] + ": " + ui.money(r["avg_rate"]) for _, r in fg.iterrows() if r["avg_rate"] > 0)
        st.caption("Your average selling rates so far, per bundle  →  " + rates)
    lines = editor("inv_lines_" + str(n), pre["lines"] if pre else blank_lines())
    valid = clean(lines)
    gross = float((valid["Bundles"] * valid["Rate (PKR)"]).sum())
    line_disc = float(valid["Discount (PKR)"].sum())

    if mode == "edit":
        d1, _, _ = st.columns(3)
        inv_disc = d1.number_input("Discount On The Whole Invoice (PKR)", min_value=0.0, step=10.0,
                                   value=float(pre["discount"]), key="inv_disc_" + str(n))
        received, method = 0.0, None
    else:
        d1, d2, d3 = st.columns(3)
        inv_disc = d1.number_input("Discount On The Whole Invoice (PKR)", min_value=0.0, step=10.0,
                                   value=float(pre["discount"]) if pre else 0.0, key="inv_disc_" + str(n))
        received = d2.number_input("Payment Received Now (PKR)", min_value=0.0, step=100.0, key="inv_rec_" + str(n))
        method = d3.selectbox("Payment Method", db.METHODS, key="inv_meth_" + str(n))
    net = gross - line_disc - float(inv_disc)

    m1, m2, m3 = st.columns(3)
    m1.metric("Gross", "PKR " + ui.money(gross))
    m2.metric("Discounts", "PKR " + ui.money(line_disc + float(inv_disc)))
    m3.metric("Invoice Total", "PKR " + ui.money(net))

    label = "Save Changes" if mode == "edit" else "Save Invoice"
    if st.button(label, type="primary", key="inv_save_" + str(n)):
        no = inv_no.strip()
        others = [x for x in existing if not (mode == "edit" and x == pre["invoice_no"])]
        got = 0.0
        if mode == "edit":
            got = float(summ.loc[summ["id"] == pre["invoice_id"], "received"].iloc[0])
        if not cust:
            st.error("Choose a customer.")
        elif not no:
            st.error("Enter an invoice number.")
        elif no in others:
            st.error("Invoice " + no + " already exists. Use a different number.")
        elif valid.empty:
            st.error("Add at least one item with product, bundles and rate.")
        elif net <= 0:
            st.error("The invoice total must be more than zero.")
        elif float(received) > net + 0.01:
            st.error("Payment received cannot be more than the invoice total.")
        elif mode == "edit" and net < got - 0.01:
            st.error("The total cannot be less than the payments already received (PKR " + ui.money(got) + ").")
        else:
            try:
                cust_id = int(cid_by_name[cust])
                head = {"invoice_no": no, "invoice_date": inv_date.isoformat(),
                        "customer_id": cust_id, "invoice_discount": float(inv_disc)}
                if mode == "edit":
                    inv_id = int(pre["invoice_id"])
                    old = db.get("invoice_lines", order="id")
                    old_ids = old.loc[old["invoice_id"] == inv_id, "id"].tolist()
                    db.insert("invoice_lines", line_rows(valid, "invoice_id", inv_id))
                    db.delete_ids("invoice_lines", old_ids)
                    db.update("invoices", inv_id, head)
                else:
                    inv_id = int(db.insert("invoices", head)[0]["id"])
                    try:
                        db.insert("invoice_lines", line_rows(valid, "invoice_id", inv_id))
                    except Exception:
                        db.delete("invoices", inv_id)
                        raise
                    if float(received) > 0:
                        db.insert("payments", {"payment_date": inv_date.isoformat(), "invoice_id": inv_id,
                                               "customer_id": cust_id, "amount": float(received), "method": method})
                    if mode == "order":
                        db.update("sale_orders", pre["order_id"], {"status": "Invoiced", "invoice_id": inv_id})
                st.session_state.pop("inv_pre", None)
                st.session_state["inv_n"] = n + 1
                st.session_state["flash"] = "Invoice " + no + (" updated." if mode == "edit" else " saved (PKR " + ui.money(net) + ").")
                if mode != "new":
                    ui.goto("sales_tab", "Invoices")
                st.rerun()
            except Exception as e:
                st.error("Could not save the invoice: " + str(e))

# ================================================================== INVOICES
elif section == "Invoices":
    def edit_invoice(r):
        il = db.get("invoice_lines", order="id")
        il = il[il["invoice_id"] == r["id"]]
        st.session_state["inv_pre"] = {
            "mode": "edit", "invoice_id": int(r["id"]), "invoice_no": r["invoice_no"],
            "date": pd.to_datetime(r["invoice_date"]).date(), "customer": r["customer_name"],
            "discount": float(r["invoice_discount"]), "lines": lines_frame(il)}
        st.session_state["inv_n"] = st.session_state.get("inv_n", 0) + 1
        ui.goto("sales_tab", "New Invoice")
        st.rerun()

    def delete_invoice(r):
        if orders is not None:
            db.update_where("sale_orders", "invoice_id", int(r["id"]), {"status": "Pending"})
        db.delete_where("payments", "invoice_id", int(r["id"]))
        db.delete("invoices", int(r["id"]))

    def add_payment(r):
        st.session_state["pay_pre"] = r["invoice_no"]
        ui.goto("sales_tab", "Payments")
        st.rerun()

    def show_items(r):
        il = db.get("invoice_lines", order="id")
        il = il[il["invoice_id"] == r["id"]]
        f = lines_frame(il)
        f["Amount"] = f["Bundles"] * f["Rate (PKR)"] - f["Discount (PKR)"]
        ui.table(ui.fmt(f, ["Bundles", "Rate (PKR)", "Discount (PKR)", "Amount"], 2))
        if r["invoice_discount"] > 0:
            st.caption("Discount on the whole invoice: PKR " + ui.money(r["invoice_discount"]))

    if summ.empty:
        st.info("No invoices yet.")
    else:
        owed = float(summ.loc[summ["balance_due"] > 0, "balance_due"].sum())
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Invoices", str(len(summ)))
        k2.metric("Billed", "PKR " + ui.money(summ["net_amount"].sum()))
        k3.metric("Received", "PKR " + ui.money(summ["received"].sum()))
        k4.metric("Receivables", "PKR " + ui.money(owed))
        f1, f2 = st.columns([2, 1])
        q = f1.text_input("Search", placeholder="Invoice number or customer", key="inv_search")
        stat = f2.multiselect("Status", ["Unpaid", "Partial", "Paid"], default=["Unpaid", "Partial", "Paid"], key="inv_status")
        v = summ[summ["status"].isin(stat)]
        if q:
            v = v[v["invoice_no"].str.contains(q, case=False, na=False) |
                  v["customer_name"].str.contains(q, case=False, na=False)]
        v = v.sort_values("id", ascending=False)
        ui.entity_table(
            "inv", v,
            [("Invoice", "invoice_no", None), ("Date", "invoice_date", None), ("Customer", "customer_name", None),
             ("Amount", "net_amount", 0), ("Received", "received", 0), ("Balance Receivable", "balance_due", 0),
             ("Status", "status", None)],
            on_edit=edit_invoice, on_delete=delete_invoice,
            extras=[("Add Payment", add_payment, lambda r: r["balance_due"] > 0)],
            detail=("View Items", show_items),
            label=lambda r: r["invoice_no"] + "  ·  " + r["customer_name"])

# =============================================================== SALE ORDERS
elif section == "Sale Orders":
    if orders is None:
        st.warning("Sale Orders need a one-time database update. Run the file orca_update_1.sql in "
                   "Supabase (SQL Editor), then refresh this page.")
    else:
        so_pre = st.session_state.get("so_pre")
        sn = st.session_state.setdefault("so_n", 0)
        pending = orders[orders["status"] == "Pending"] if not orders.empty else orders
        k1, k2, k3 = st.columns(3)
        k1.metric("Pending Orders", str(len(pending)))
        k2.metric("Pending Value", "PKR " + ui.money(pending["net_amount"].sum() if not pending.empty else 0))
        k3.metric("Invoiced Orders", str(int((orders["status"] == "Invoiced").sum()) if not orders.empty else 0))
        st.caption("A sale order is a pending, not-yet-delivered order. It does not count as a receivable until you convert it to an invoice.")

        title = "New Sale Order" if not so_pre else "Edit Sale Order " + so_pre["order_no"]
        with st.expander(title, expanded=bool(so_pre)):
            existing_o = orders["order_no"].tolist() if not orders.empty else []
            a, b, c = st.columns([1, 1, 2])
            o_no = a.text_input("Order No.", value=so_pre["order_no"] if so_pre else db.next_no(existing_o, "SO#"),
                                key="so_no_" + str(sn))
            o_date = b.date_input("Order Date", value=so_pre["date"] if so_pre else dt.date.today(), key="so_date_" + str(sn))
            oidx = cust_names.index(so_pre["customer"]) if so_pre and so_pre["customer"] in cust_names else None
            o_cust = c.selectbox("Customer", cust_names, index=oidx, placeholder="Choose A Customer", key="so_cust_" + str(sn))
            o_lines = editor("so_lines_" + str(sn), so_pre["lines"] if so_pre else blank_lines())
            ov = clean(o_lines)
            og = float((ov["Bundles"] * ov["Rate (PKR)"]).sum())
            old_ = float(ov["Discount (PKR)"].sum())
            x1, x2, x3 = st.columns(3)
            o_disc = x1.number_input("Discount On The Whole Order (PKR)", min_value=0.0, step=10.0,
                                     value=float(so_pre["discount"]) if so_pre else 0.0, key="so_disc_" + str(sn))
            o_del = x2.date_input("Expected Delivery (Optional)", value=so_pre["delivery"] if so_pre else None,
                                  key="so_del_" + str(sn))
            o_notes = x3.text_input("Notes (Optional)", value=so_pre["notes"] if so_pre else "", key="so_notes_" + str(sn))
            o_net = og - old_ - float(o_disc)
            st.caption("Order total: PKR " + ui.money(o_net))
            bl, br = st.columns([1, 5])
            if bl.button("Save Order", type="primary", key="so_save_" + str(sn)):
                no = o_no.strip()
                others = [x for x in existing_o if not (so_pre and x == so_pre["order_no"])]
                if not o_cust:
                    st.error("Choose a customer.")
                elif not no:
                    st.error("Enter an order number.")
                elif no in others:
                    st.error("Order " + no + " already exists.")
                elif ov.empty:
                    st.error("Add at least one item with product, bundles and rate.")
                else:
                    try:
                        head = {"order_no": no, "order_date": o_date.isoformat(), "customer_id": int(cid_by_name[o_cust]),
                                "order_discount": float(o_disc), "notes": o_notes.strip() or None,
                                "delivery_date": o_del.isoformat() if o_del else None}
                        if so_pre:
                            oid = int(so_pre["order_id"])
                            old = db.get("sale_order_lines", order="id")
                            old_ids = old.loc[old["order_id"] == oid, "id"].tolist()
                            db.insert("sale_order_lines", line_rows(ov, "order_id", oid))
                            db.delete_ids("sale_order_lines", old_ids)
                            db.update("sale_orders", oid, head)
                        else:
                            oid = int(db.insert("sale_orders", head)[0]["id"])
                            try:
                                db.insert("sale_order_lines", line_rows(ov, "order_id", oid))
                            except Exception:
                                db.delete("sale_orders", oid)
                                raise
                        st.session_state.pop("so_pre", None)
                        st.session_state["so_n"] = sn + 1
                        st.session_state["flash"] = "Sale order " + no + " saved."
                        st.rerun()
                    except Exception as e:
                        st.error("Could not save the order: " + str(e))
            if so_pre and br.button("Cancel Editing", key="so_cancel_" + str(sn)):
                st.session_state.pop("so_pre", None)
                st.session_state["so_n"] = sn + 1
                st.rerun()

        def order_lines(r):
            ol = db.get("sale_order_lines", order="id")
            return ol[ol["order_id"] == r["id"]]

        def convert_order(r):
            st.session_state["inv_pre"] = {
                "mode": "order", "order_id": int(r["id"]), "order_no": r["order_no"], "customer": r["customer_name"],
                "discount": float(r["order_discount"]), "lines": lines_frame(order_lines(r))}
            st.session_state["inv_n"] = st.session_state.get("inv_n", 0) + 1
            ui.goto("sales_tab", "New Invoice")
            st.rerun()

        def edit_order(r):
            st.session_state["so_pre"] = {
                "order_id": int(r["id"]), "order_no": r["order_no"], "date": pd.to_datetime(r["order_date"]).date(),
                "customer": r["customer_name"], "discount": float(r["order_discount"]),
                "delivery": pd.to_datetime(r["delivery_date"]).date() if pd.notna(r["delivery_date"]) else None,
                "notes": r["notes"] if pd.notna(r["notes"]) else "", "lines": lines_frame(order_lines(r))}
            st.session_state["so_n"] = st.session_state.get("so_n", 0) + 1
            st.rerun()

        def cancel_order(r):
            db.update("sale_orders", int(r["id"]), {"status": "Cancelled"})
            st.session_state["tv_so"] = st.session_state.get("tv_so", 0) + 1
            st.session_state["flash"] = "Order " + r["order_no"] + " cancelled."
            st.rerun()

        def order_items(r):
            f = lines_frame(order_lines(r))
            f["Amount"] = f["Bundles"] * f["Rate (PKR)"] - f["Discount (PKR)"]
            ui.table(ui.fmt(f, ["Bundles", "Rate (PKR)", "Discount (PKR)", "Amount"], 2))

        st.markdown("#### Orders")
        if orders.empty:
            st.info("No sale orders yet.")
        else:
            f1, f2 = st.columns([2, 1])
            q = f1.text_input("Search", placeholder="Order number or customer", key="so_search")
            stat = f2.multiselect("Status", ["Pending", "Invoiced", "Cancelled"], default=["Pending"], key="so_status")
            v = orders[orders["status"].isin(stat)]
            if q:
                v = v[v["order_no"].str.contains(q, case=False, na=False) |
                      v["customer_name"].str.contains(q, case=False, na=False)]
            v = v.sort_values("id", ascending=False)
            ui.entity_table(
                "so", v,
                [("Order", "order_no", None), ("Date", "order_date", None), ("Customer", "customer_name", None),
                 ("Expected Delivery", "delivery_date", None), ("Amount", "net_amount", 0), ("Status", "status", None)],
                on_edit=edit_order, can_edit=lambda r: r["status"] == "Pending",
                extras=[("Convert To Invoice", convert_order, lambda r: r["status"] == "Pending"),
                        ("Cancel Order", cancel_order, lambda r: r["status"] == "Pending")],
                detail=("View Items", order_items),
                label=lambda r: r["order_no"] + "  ·  " + r["customer_name"],
                on_delete=lambda r: db.delete("sale_orders", int(r["id"])))

# ================================================================== PAYMENTS
elif section == "Payments":
    open_inv = summ[summ["balance_due"] > 0].sort_values("id", ascending=False) if not summ.empty else summ
    if open_inv.empty:
        st.success("All invoices are fully paid.")
    else:
        labels = {}
        for _, r in open_inv.iterrows():
            labels[r["invoice_no"] + "  ·  " + r["customer_name"] + "  ·  due " + ui.money(r["balance_due"])] = r
        pre_no = st.session_state.pop("pay_pre", None)
        if pre_no:
            for lab, r in labels.items():
                if r["invoice_no"] == pre_no:
                    st.session_state["pay_inv"] = lab
        pick = st.selectbox("Invoice Being Paid", list(labels.keys()), index=None,
                            placeholder="Choose An Unpaid Invoice", key="pay_inv")
        if pick:
            r = labels[pick]
            due = float(r["balance_due"])
            p1, p2, p3 = st.columns(3)
            amt = p1.number_input("Amount Received (PKR)", min_value=0.0, value=due, step=100.0,
                                  key="pay_amt_" + str(int(r["id"])))
            pdate = p2.date_input("Date", value=dt.date.today(), key="pay_date")
            pmeth = p3.selectbox("Method", db.METHODS, key="pay_meth")
            pnotes = st.text_input("Notes (Optional)", key="pay_notes")
            if st.button("Record Payment", type="primary", key="pay_save"):
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

    st.markdown("#### Payment History")
    pay = db.get("payments", order="id", desc=True)
    if pay.empty:
        st.info("No payments recorded yet.")
    else:
        h = pay.copy()
        h["invoice_no"] = h["invoice_id"].map(db.name_map(summ, "invoice_no"))
        h["customer_name"] = h["customer_id"].map(db.name_map(customers))

        def check_payment(payload, rec):
            if payload["amount"] <= 0:
                return "Enter an amount."
            row = summ[summ["id"] == rec["invoice_id"]]
            if not row.empty and payload["amount"] > float(row.iloc[0]["balance_due"]) + float(rec["amount"]) + 0.01:
                return "That is more than the invoice balance."
            return None

        ui.entity_table(
            "pay", h,
            [("Date", "payment_date", None), ("Invoice", "invoice_no", None), ("Customer", "customer_name", None),
             ("Amount", "amount", 0), ("Method", "method", None), ("Notes", "notes", None)],
            table="payments",
            fields=[{"col": "payment_date", "label": "Date", "kind": "date"},
                    {"col": "amount", "label": "Amount (PKR)", "kind": "num", "step": 100.0},
                    {"col": "method", "label": "Method", "kind": "choice", "options": db.METHODS},
                    {"col": "notes", "label": "Notes", "kind": "text"}],
            validate=check_payment,
            label=lambda r: str(r["invoice_no"]) + "  ·  " + str(r["customer_name"]) + "  ·  PKR " + ui.money(r["amount"]))
