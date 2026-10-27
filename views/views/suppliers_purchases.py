import datetime as dt

import pandas as pd
import streamlit as st

import db
import ui

ui.header("Suppliers & Purchases", "Your suppliers, raw material purchases and what you've bought from each")

raw = db.get("v_raw_stock", order="id")
rname = db.name_map(raw)
try:
    suppliers = db.get("suppliers", order="name")
except Exception:
    suppliers = None

section = ui.sections(["Suppliers", "Purchases"], "sup_pur_tab")

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
        sdf = suppliers.copy()
        if not sdf.empty:
            sdf["key"] = sdf["name"].str.strip().str.lower()
            sdf = sdf.merge(tot, on="key", how="left")
            sdf["purchased"] = sdf["purchased"].fillna(0)

        k1, k2 = st.columns(2)
        k1.metric("Suppliers", str(len(suppliers)))
        k2.metric("Total Purchased", "PKR " + ui.money(sdf["purchased"].sum() if not sdf.empty else 0))

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
                 ("Last Purchase", "last_purchase", None)],
                table="suppliers",
                fields=[{"col": "name", "label": "Supplier Name", "required": True},
                        {"col": "category", "label": "What They Supply"},
                        {"col": "contact_person", "label": "Contact Person"},
                        {"col": "phone", "label": "Phone"},
                        {"col": "address", "label": "Address / Area"}],
                label=lambda r: str(r["name"]))

# ================================================================== PURCHASES
else:
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
            if st.button("Save Purchase", type="primary", key="pur_save_" + str(n)):
                supplier = sup_new.strip() or sup_pick or None
                if not item:
                    st.error("Choose a raw material.")
                elif qty <= 0:
                    st.error("Enter a quantity.")
                else:
                    try:
                        rid = int(raw.loc[raw["name"] == item, "id"].iloc[0])
                        db.insert("purchases", {"purchase_date": pdate.isoformat(), "supplier": supplier,
                                                "raw_material_id": rid, "qty": float(qty), "unit_cost": float(cost),
                                                "ref": ref.strip() or None, "notes": notes.strip() or None})
                        if supplier and suppliers is not None and supplier.lower() not in [x.lower() for x in sup_names]:
                            try:
                                db.insert("suppliers", {"name": supplier})
                            except Exception:
                                pass
                        st.session_state["pur_n"] = n + 1
                        st.session_state["flash"] = "Purchase saved: " + ui.money(qty) + " × " + item + "."
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
        ui.entity_table(
            "pur", h,
            [("Date", "purchase_date", None), ("Supplier", "supplier", None), ("Raw Material", "material", None),
             ("Quantity", "qty", 0), ("Unit Cost", "unit_cost", 2), ("Total", "total", 0), ("Reference", "ref", None)],
            table="purchases",
            fields=[{"col": "purchase_date", "label": "Date", "kind": "date"},
                    {"col": "supplier", "label": "Supplier"},
                    {"col": "raw_material_id", "label": "Raw Material", "kind": "select", "options": rname},
                    {"col": "qty", "label": "Quantity", "kind": "num"},
                    {"col": "unit_cost", "label": "Unit Cost (PKR)", "kind": "num", "step": 0.1},
                    {"col": "ref", "label": "Invoice / Reference"},
                    {"col": "notes", "label": "Notes"}],
            label=lambda r: str(r["purchase_date"]) + "  ·  " + str(r["material"]) + "  ·  " + ui.money(r["qty"]))
