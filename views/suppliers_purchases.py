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
            qty = d.number_input("Quantity", min_value=0.0, 
