import datetime as dt

import pandas as pd
import streamlit as st

import db
import ui

ui.header("Suppliers & Purchases", "Your suppliers, raw material purchases and what you owe each")

raw = db.get("v_raw_stock", order="id")
rname = db.name_map(raw)
try:
    suppliers = db.get("suppliers", order="name")
except Exception:
    suppliers = None

section = ui.sections(["Suppliers", "Purchases", "Supplier Payments"], "sup_pur_tab")

# ================================================================== SUPPLIERS
if section == "Suppliers":
    if suppliers is None:
        st.warning("Suppliers need a one-time database update. Run the file orca_update_1.sql in "
                   "Supabase (SQL Editor), then refresh this page.")
    else:
        pur_all = db.get("purchases", order="id")
        if pur_all.empty:
            tot = pd.DataFrame(columns=["key", "purchased", "last_purchase"])
        else:
            pp = pur_all.assign(key=pur_all["supplier"].fillna("").str.strip().str.lower(),
                                amount=pur_all["qty"] * pur_all["unit_cost"])
            tot = pp.groupby("key").agg(purchased=("amount", "sum"), last_purchase=("purchase_date", "max")).reset_index()
        payables = db.get_payables()
        sdf = suppliers.copy()
        if not sdf.empty:
            sdf["key"] = sdf["name"].str.strip().str.lower()
            sdf = sdf.merge(tot, on="key", how="left")
            sdf["purchased"] = sdf["purchased"].fillna(0)
            if not payables.empty:
                pay2 = payables.copy()
                pay2["key"] = pay2["supplier"].str.strip().str.lower()
                sdf = sdf.merge(pay2[["key", "payable"]], on="key", how="left")
            else:
                sdf["payable"] = 0.0
            sdf["payable"] = sdf["payable"].fillna(0.0)

        k1, k2, k3 = st.columns(3)
        k1.metric("Suppliers", str(len(suppliers)))
        k2.metric("Total Purchased", "PKR " + ui.money(sdf["purchased"].sum() if not sdf.empty else 0))
        k3.metric("Total Owed To Suppliers", "PKR " + ui.money(sdf["payable"].sum() if not sdf.empty else 0))

        with st.expander("Add A New Supplier"):
            n = st.session_state.setdefault("sup_n", 0)
            a, b = st.columns(2)
            sname = a.text_input("Supplier Name", key="s_name_" + str(n))
            scat = b.text_input("What They Supply (Optional)", key="s_cat_" + str(n))
            c, d = st.columns(2)
            sper = c.text_input("Contact Person", key="s_per_" + str(n))
            sph = d.text_input("Phone", key="s_ph_" + str(n))
            sadr = st.text_input("Address / Area", key="s_adr_" + str(n))
            if st.button("Add Supplier", type="primary", key="s_save_" + str(n)):
                nm = sname.strip()
                if not nm:
                    st.error("Enter the supplier name.")
                elif not suppliers.empty and nm.lower() in suppliers["name"].str.lower().tolist():
                    st.error("A supplier with this name already exists.")
                else:
                    try:
                        db.insert("suppliers", {"name": nm, "category": scat.strip() or None,
                                                "contact_person": sper.strip() or None,
                                                "phone": sph.strip() or None, "address": sadr.strip() or None})
                        st.session_state["sup_n"] = n + 1
                        st.session_state["flash"] = "Supplier " + nm + " added."
                        st.rerun()
                    except Exception as e:
                        st.error("Could not add the supplier: " + str(e))

        if suppliers.empty:
            st.info("No suppliers yet.")
        else:
            ui.entity_table(
                "sup", sdf.sort_values("name"),
                [("Supplier", "name", None), ("Supplies", "category", None), ("Contact", "contact_person", None),
                 ("Phone", "phone", None), ("Address", "address", None), ("Total Purchased", "purchased", 0),
                 ("Owed", "payable", 0), ("Last Purchase", "last_purchase", None)],
                table="suppliers",
                fields=[{"col": "name", "label": "Supplier Name", "required": True},
                        {"col": "category", "label": "What They Supply"},
                        {"col": "contact_person", "label": "Contact Person"},
                        {"col": "phone", "label": "Phone"},
                        {"col": "address", "label": "Address / Area"}],
                label=lambda r: str(r["name"]))

# ================================================================== PURCHASES
elif section == "Purchases":
    if raw.empty:
        st.info("Add raw materials first.")
    else:
        with st.expander("Record A Purchase", expanded=True):
            n = st.session_state.setdefault("pur_n", 0)
            a, b, c = st.columns(3)
            pdate = a.date_input("Date", value=dt.date.today(), key="pur_d_" + str(n))
            item = b.selectbox("Raw Material", raw["name"].tolist(), index=None, placeholder="Choose", key="pur_i_" + str(n))
            sup_names = suppliers["name"].tolist() if suppliers is not None and not suppliers.empty else []
            sup_pick = c.selectbox("Supplier", sup_names, index=None, placeholder="Choose Or Type Below", key="pur_sp_" + str(n))
            sup_new = st.text_input("Or Type A New Supplier (Optional)", key="pur_s_" + str(n))
            d, e, f = st.columns(3)
            qty = d.number_input("Quantity", min_value=0.0, step=1.0, key="pur_q_" + str(n))
            cost = e.number_input("Unit Cost (PKR)", min_value=0.0, step=0.1, format="%.2f", key="pur_c_" + str(n))
            ref = f.text_input("Invoice / Reference", key="pur_r_" + str(n))
            notes = st.text_input("Notes (Optional)", key="pur_n_" + str(n))
            if item:
                r = raw[raw["name"] == item].iloc[0]
                old_q = float(r["opening_stock"]) + float(r["purchased_qty"])
                old_v = float(r["opening_stock"]) * float(r["opening_unit_cost"]) + float(r["purchase_value"])
                new_q = old_q + float(qty)
                new_avg = (old_v + float(qty) * float(cost)) / new_q if new_q else 0
                st.caption("Total this purchase: PKR " + ui.money(qty * cost, 2) + "   ·   Average cost now: " +
                           ui.money(r["avg_cost"], 2) + "  →  after this purchase: " + ui.money(new_avg, 2))
                st.caption("This also creates a new batch dated " + pdate.isoformat() +
                          ", which Production and Raw Material Damages will use oldest-first.")

            st.markdown("**Payment**")
            pay_mode = st.radio("How Is This Purchase Being Paid?", ["Paid In Full Now", "On Credit (Pay Later)"],
                                horizontal=True, key="pur_mode_" + str(n))
            total = float(qty) * float(cost)
            paid_amount = paid_sales = paid_profit = 0.0
            if pay_mode == "Paid In Full Now":
                paid_amount = total
                if total > 0:
                    st.caption("Total to pay: PKR " + ui.money(total, 2) + ". Tell us where the money came from — "
                              "this is just for your own tracking, it never changes your profit numbers.")
                    p1, p2 = st.columns(2)
                    paid_sales = p1.number_input("Paid From Sales Money (PKR)", min_value=0.0, max_value=float(total),
                                                 value=float(total), step=10.0, key="pur_ps_" + str(n))
                    paid_profit = max(total - paid_sales, 0.0)
                    p2.metric("Paid From Your Own Pocket / Profit Money", "PKR " + ui.money(paid_profit, 2))
                else:
                    st.caption("Enter the quantity and unit cost above to set the payment split.")
            else:
                st.caption("Nothing is paid yet — the supplier will be marked as owed PKR " + ui.money(total, 2) +
                          ". You can pay it later from the Supplier Payments tab.")

            if st.button("Save Purchase", type="primary", key="pur_save_" + str(n)):
                supplier = sup_new.strip() or sup_pick or None
                if not item:
                    st.error("Choose a raw material.")
                elif qty <= 0:
                    st.error("Enter a quantity.")
                else:
                    try:
                        rid = int(raw.loc[raw["name"] == item, "id"].iloc[0])
                        db.record_purchase(pdate.isoformat(), supplier, rid, float(qty), float(cost),
                                           ref.strip() or None, notes.strip() or None,
                                           paid_amount=float(paid_amount), paid_from_sales=float(paid_sales),
                                           paid_from_profit=float(paid_profit))
                        if supplier and suppliers is not None and supplier.lower() not in [x.lower() for x in sup_names]:
                            try:
                                db.insert("suppliers", {"name": supplier})
                            except Exception:
                                pass
                        st.session_state["pur_n"] = n + 1
                        tail = " (paid in full)." if pay_mode == "Paid In Full Now" else " (on credit)."
                        st.session_state["flash"] = "Purchase saved: " + ui.money(qty) + " × " + item + tail
                        st.rerun()
                    except Exception as ex:
                        st.error("Could not save: " + str(ex))
    st.markdown("#### Purchase History")
    pur = db.get("purchases", order="id", desc=True)
    if pur.empty:
        st.info("No purchases recorded yet.")
    else:
        h = pur.copy()
        h["material"] = h["raw_material_id"].map(rname)
        h["total"] = h["qty"] * h["unit_cost"]
        h["paid_amount"] = h["paid_amount"].fillna(h["total"]) if "paid_amount" in h.columns else h["total"]
        h["owed"] = h["total"] - h["paid_amount"]

        def status_row(r):
            if r["paid_amount"] >= r["total"] - 0.01:
                return "Paid"
            if r["paid_amount"] <= 0.01:
                return "Credit"
            return "Partial"

        h["status"] = h.apply(status_row, axis=1)
        ui.entity_table(
            "pur", h,
            [("Date", "purchase_date", None), ("Supplier", "supplier", None), ("Raw Material", "material", None),
             ("Quantity", "qty", 0), ("Unit Cost", "unit_cost", 2), ("Total", "total", 0),
             ("Paid", "paid_amount", 0), ("Owed", "owed", 0), ("Status", "status", None), ("Reference", "ref", None)],
            table="purchases",
            fields=[{"col": "supplier", "label": "Supplier"},
                    {"col": "ref", "label": "Invoice / Reference"},
                    {"col": "notes", "label": "Notes"}],
            label=lambda r: str(r["purchase_date"]) + "  ·  " + str(r["material"]) + "  ·  " + ui.money(r["qty"]),
            can_delete=lambda r: False)
        st.caption("Quantity and cost can't be changed here, since they've already become a batch that may be in "
                  "use. If a supplier sends more at the same price, use 'Replace (Same Price)' in Stock & Production "
                  "→ Batches. If a purchase was recorded as 'On Credit' and needs to be paid, use the Supplier "
                  "Payments tab. If something was entered completely wrong, let me know and we'll fix it directly.")

# ============================================================ SUPPLIER PAYMENTS
else:
    payables = db.get_payables()
    owing = payables[payables["payable"] > 0.01] if not payables.empty else payables

    k1, k2 = st.columns(2)
    k1.metric("Total Owed To Suppliers", "PKR " + ui.money(payables["payable"].sum() if not payables.empty else 0))
    k2.metric("Suppliers With A Balance", str(len(owing)) if owing is not None and not owing.empty else "0")

    if owing is None or owing.empty:
        st.success("No outstanding balance with any supplier.")
    else:
        labels = {}
        for _, r in owing.sort_values("payable", ascending=False).iterrows():
            labels[r["supplier"] + "  ·  owed PKR " + ui.money(r["payable"])] = r
        pick = st.selectbox("Supplier Being Paid", list(labels.keys()), index=None,
                            placeholder="Choose A Supplier", key="sp_pick")
        if pick:
            r = labels[pick]
            due = float(r["payable"])
            p1, p2, p3 = st.columns(3)
            amt = p1.number_input("Amount Paid (PKR)", min_value=0.0, max_value=due, value=due, step=100.0, key="sp_amt")
            pdate = p2.date_input("Date", value=dt.date.today(), key="sp_date")
            pmeth = p3.selectbox("Method", db.METHODS, key="sp_meth")
            st.caption("Tell us where this money came from — personal tracking only, it never changes your profit numbers.")
            q1, q2 = st.columns(2)
            pay_sales = q1.number_input("Paid From Sales Money (PKR)", min_value=0.0, max_value=float(amt) if amt > 0 else 0.0,
                                        value=float(amt), step=10.0, key="sp_ps")
            pay_profit = max(amt - pay_sales, 0.0)
            q2.metric("Paid From Your Own Pocket / Profit Money", "PKR " + ui.money(pay_profit, 2))
            pnotes = st.text_input("Notes (Optional)", key="sp_notes")
            if st.button("Record Supplier Payment", type="primary", key="sp_save"):
                if amt <= 0:
                    st.error("Enter an amount.")
                elif amt > due + 0.01:
                    st.error("That is more than what's owed (PKR " + ui.money(due) + ").")
                else:
                    try:
                        db.record_supplier_payment(pdate.isoformat(), r["supplier"], float(amt), float(pay_sales),
                                                   float(pay_profit), pmeth, pnotes.strip() or None)
                        st.session_state["flash"] = "Payment of PKR " + ui.money(amt) + " recorded for " + r["supplier"] + "."
                        st.rerun()
                    except Exception as e:
                        st.error("Could not save the payment: " + str(e))

    st.markdown("#### Supplier Payment History")
    sp = db.get("supplier_payments", order="id", desc=True)
    if sp.empty:
        st.info("No supplier payments recorded yet.")
    else:
        ui.entity_table(
            "sp", sp,
            [("Date", "payment_date", None), ("Supplier", "supplier", None), ("Amount", "amount", 0),
             ("From Sales", "paid_from_sales", 0), ("From Profit", "paid_from_profit", 0),
             ("Method", "method", None), ("Notes", "notes", None)],
            table="supplier_payments",
            fields=[{"col": "amount", "label": "Amount (PKR)", "kind": "num", "step": 100.0},
                    {"col": "method", "label": "Method", "kind": "choice", "options": db.METHODS},
                    {"col": "notes", "label": "Notes"}],
            label=lambda r: str(r["payment_date"]) + "  ·  " + str(r["supplier"]) + "  ·  PKR " + ui.money(r["amount"]))
