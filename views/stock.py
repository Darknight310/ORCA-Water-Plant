import datetime as dt

import pandas as pd
import streamlit as st

import db
import ui

ui.header("Stock & Production", "Finished goods, raw materials, purchases, production and damages")

products = db.get("products", order="id")
raw = db.get("v_raw_stock", order="id")
fg = db.get("v_product_stock", order="id")
recipe = db.get("recipe", order="id")

t_fg, t_raw, t_rec, t_pur, t_prod, t_dam = st.tabs(
    ["Finished goods", "Raw materials", "Recipe", "Purchases", "Production", "Damages"])

pname = db.name_map(products)
rname = db.name_map(raw)


def settings_form(df, table_name, key, level_col, unit_label):
    """Physical count + alert level for one item."""
    if df.empty:
        return
    with st.expander("Physical count & alert level"):
        st.caption("Enter what you actually counted. The app adjusts the starting stock so the balance matches your count.")
        name = st.selectbox("Item", df["name"].tolist(), index=None, placeholder="Choose an item",
                            key="set_item_" + key)
        if name:
            r = df[df["name"] == name].iloc[0]
            rid = int(r["id"])
            cur = 0.0 if pd.isna(r[level_col]) else float(r[level_col])
            a, b = st.columns(2)
            count = a.number_input("Counted quantity (" + unit_label + ")", min_value=0.0,
                                   value=float(r["balance"]), step=1.0, key="set_cnt_" + key + str(rid))
            level = b.number_input("Alert me when stock falls to (" + unit_label + ")", min_value=0.0,
                                   value=cur, step=1.0, key="set_lvl_" + key + str(rid))
            if st.button("Save", type="primary", key="set_save_" + key + str(rid)):
                new_open = float(count) - (float(r["balance"]) - float(r["opening_stock"]))
                try:
                    db.update(table_name, rid, {"opening_stock": new_open, level_col: float(level)})
                    st.session_state["flash"] = name + " updated."
                    st.rerun()
                except Exception as e:
                    st.error("Could not save: " + str(e))


# ------------------------------------------------------------- finished goods
with t_fg:
    if fg.empty:
        st.info("No products yet.")
    else:
        k1, k2, k3 = st.columns(3)
        k1.metric("Finished goods value", "PKR " + ui.money(fg["stock_value"].sum()))
        k2.metric("Bundles in stock", ui.money(fg["balance"].sum()))
        k3.metric("Products running low", str(int((fg["status"] == "LOW").sum())))
        v = fg.assign(margin=fg["avg_rate"] - fg["std_cost"])
        v = v[["name", "opening_stock", "produced", "sold", "damaged", "balance", "std_cost", "avg_rate",
               "margin", "stock_value", "status"]]
        v = ui.fmt(v, ["opening_stock", "produced", "sold", "damaged", "balance", "stock_value"])
        v = ui.fmt(v, ["std_cost", "avg_rate", "margin"], 2)
        v.columns = ["Product", "Opening", "Produced", "Sold", "Damaged", "In stock", "Cost / bundle",
                     "Avg sell rate", "Margin / bundle", "Stock value", "Status"]
        ui.table(v)
        st.caption("Cost per bundle = recipe × average raw material cost. Alerts show 'Set level' until you set one.")
        settings_form(fg, "products", "fg", "min_stock", "bundles")

# --------------------------------------------------------------- raw materials
with t_raw:
    if raw.empty:
        st.info("No raw materials yet.")
    else:
        k1, k2, k3 = st.columns(3)
        k1.metric("Raw material value", "PKR " + ui.money(raw["stock_value"].sum()))
        k2.metric("Items", str(len(raw)))
        k3.metric("Items running low", str(int((raw["status"] == "LOW").sum())))
        v = raw[["name", "unit", "opening_stock", "purchased_qty", "used_qty", "damaged_qty", "balance",
                 "avg_cost", "stock_value", "reorder_level", "status"]]
        v = ui.fmt(v, ["opening_stock", "purchased_qty", "used_qty", "damaged_qty", "balance", "stock_value", "reorder_level"])
        v = ui.fmt(v, ["avg_cost"], 2)
        v.columns = ["Raw material", "Unit", "Opening", "Purchased", "Used", "Damaged", "In stock",
                     "Avg cost", "Stock value", "Alert level", "Status"]
        ui.table(v)
        settings_form(raw, "raw_materials", "raw", "reorder_level", "units")
    with st.expander("Add a new raw material"):
        n = st.session_state.setdefault("rm_n", 0)
        a, b, c = st.columns(3)
        nm = a.text_input("Name", key="rm_name_" + str(n))
        unit = b.text_input("Unit", value="Pcs", key="rm_unit_" + str(n))
        code = c.text_input("Code", value=db.next_code(raw["code"].tolist() if not raw.empty else [], "RM-"),
                            key="rm_code_" + str(n))
        d, e = st.columns(2)
        oq = d.number_input("Quantity you have now", min_value=0.0, step=1.0, key="rm_oq_" + str(n))
        oc = e.number_input("Cost per unit (PKR)", min_value=0.0, step=0.1, format="%.2f", key="rm_oc_" + str(n))
        st.caption("After adding it, put it into a product's recipe in the Recipe tab.")
        if st.button("Add raw material", type="primary", key="rm_save_" + str(n)):
            if not nm.strip():
                st.error("Enter a name.")
            elif not raw.empty and nm.strip().lower() in raw["name"].str.lower().tolist():
                st.error("That raw material already exists.")
            else:
                try:
                    db.insert("raw_materials", {"code": code.strip(), "name": nm.strip(), "unit": unit.strip() or "Pcs",
                                                "opening_stock": float(oq), "opening_unit_cost": float(oc)})
                    st.session_state["rm_n"] = n + 1
                    st.session_state["flash"] = nm.strip() + " added."
                    st.rerun()
                except Exception as ex:
                    st.error("Could not add: " + str(ex))

# ---------------------------------------------------------------------- recipe
with t_rec:
    st.caption("How much of each raw material goes into ONE bundle of each product. This drives production and product cost.")
    if recipe.empty:
        st.info("No recipe lines yet.")
    else:
        rc = recipe.assign(Product=recipe["product_id"].map(pname), Material=recipe["raw_material_id"].map(rname))
        pv = rc.pivot_table(index="Material", columns="Product", values="qty_per_bundle", aggfunc="sum").fillna(0)
        pv = pv.reset_index()
        ui.table(ui.fmt(pv, [c for c in pv.columns if c != "Material"], 0))
    if not products.empty and not raw.empty:
        a, b, c = st.columns(3)
        rp = a.selectbox("Product", products["name"].tolist(), index=None, placeholder="Choose", key="rec_p")
        rm = b.selectbox("Raw material", raw["name"].tolist(), index=None, placeholder="Choose", key="rec_m")
        rq = c.number_input("Quantity per bundle", min_value=0.0, step=1.0, key="rec_q")
        st.caption("Saving a quantity replaces the old one. Use 0 to remove a material from a recipe.")
        if st.button("Save recipe line", type="primary", key="rec_save"):
            if not rp or not rm:
                st.error("Choose a product and a raw material.")
            else:
                try:
                    pid = int(products.loc[products["name"] == rp, "id"].iloc[0])
                    rid = int(raw.loc[raw["name"] == rm, "id"].iloc[0])
                    db.upsert("recipe", {"product_id": pid, "raw_material_id": rid, "qty_per_bundle": float(rq)},
                              "product_id,raw_material_id")
                    st.session_state["flash"] = "Recipe updated."
                    st.rerun()
                except Exception as ex:
                    st.error("Could not save: " + str(ex))

# -------------------------------------------------------------------- purchases
with t_pur:
    if raw.empty:
        st.info("Add raw materials first.")
    else:
        n = st.session_state.setdefault("pur_n", 0)
        a, b, c = st.columns(3)
        pd_ = a.date_input("Date", value=dt.date.today(), key="pur_d_" + str(n))
        sup = b.text_input("Supplier", key="pur_s_" + str(n))
        item = c.selectbox("Raw material", raw["name"].tolist(), index=None, placeholder="Choose", key="pur_i_" + str(n))
        d, e, f = st.columns(3)
        qty = d.number_input("Quantity", min_value=0.0, step=1.0, key="pur_q_" + str(n))
        cost = e.number_input("Unit cost (PKR)", min_value=0.0, step=0.1, format="%.2f", key="pur_c_" + str(n))
        ref = f.text_input("Invoice / reference", key="pur_r_" + str(n))
        notes = st.text_input("Notes (optional)", key="pur_n_" + str(n))
        if item:
            r = raw[raw["name"] == item].iloc[0]
            old_q = float(r["opening_stock"]) + float(r["purchased_qty"])
            old_v = float(r["opening_stock"]) * float(r["opening_unit_cost"]) + float(r["purchase_value"])
            new_q = old_q + float(qty)
            new_avg = (old_v + float(qty) * float(cost)) / new_q if new_q else 0
            st.caption("Total this purchase: PKR " + ui.money(qty * cost, 2) + "   ·   Average cost now: " +
                       ui.money(r["avg_cost"], 2) + "  →  after this purchase: " + ui.money(new_avg, 2))
        if st.button("Save purchase", type="primary", key="pur_save_" + str(n)):
            if not item:
                st.error("Choose a raw material.")
            elif qty <= 0:
                st.error("Enter a quantity.")
            else:
                try:
                    rid = int(raw.loc[raw["name"] == item, "id"].iloc[0])
                    db.insert("purchases", {"purchase_date": pd_.isoformat(), "supplier": sup.strip() or None,
                                            "raw_material_id": rid, "qty": float(qty), "unit_cost": float(cost),
                                            "ref": ref.strip() or None, "notes": notes.strip() or None})
                    st.session_state["pur_n"] = n + 1
                    st.session_state["flash"] = "Purchase saved: " + ui.money(qty) + " × " + item + "."
                    st.rerun()
                except Exception as ex:
                    st.error("Could not save: " + str(ex))
    pur = db.get("purchases", order="id", desc=True)
    st.markdown("#### Purchase history")
    if pur.empty:
        st.info("No purchases recorded yet.")
    else:
        h = pur.copy()
        h["Material"] = h["raw_material_id"].map(rname)
        h["Total"] = h["qty"] * h["unit_cost"]
        show = ui.fmt(h[["purchase_date", "supplier", "Material", "qty", "unit_cost", "Total", "ref"]], ["qty", "Total"])
        show = ui.fmt(show, ["unit_cost"], 2)
        show.columns = ["Date", "Supplier", "Raw material", "Quantity", "Unit cost", "Total", "Reference"]
        ui.table(show.head(200))
        ui.delete_entry("purchases", h, lambda r: str(r["purchase_date"]) + " · " + str(r["Material"]) + " · " + ui.money(r["qty"]), "pur")

# ------------------------------------------------------------------ production
with t_prod:
    if products.empty:
        st.info("No products yet.")
    else:
        n = st.session_state.setdefault("prd_n", 0)
        a, b, c = st.columns(3)
        pdt = a.date_input("Date", value=dt.date.today(), key="prd_d_" + str(n))
        batch = b.text_input("Batch / reference", key="prd_b_" + str(n))
        prod = c.selectbox("Product made", products["name"].tolist(), index=None, placeholder="Choose", key="prd_p_" + str(n))
        d, e = st.columns([1, 2])
        bundles = d.number_input("Bundles produced", min_value=0.0, step=1.0, key="prd_q_" + str(n))
        notes = e.text_input("Notes (optional)", key="prd_n_" + str(n))
        need_ok = False
        if prod and bundles > 0:
            pid = int(products.loc[products["name"] == prod, "id"].iloc[0])
            rs = raw[["id", "name", "unit", "balance"]].rename(columns={"id": "rm_id", "name": "Material", "balance": "In stock"})
            need = recipe[recipe["product_id"] == pid].merge(rs, left_on="raw_material_id", right_on="rm_id")
            if need.empty:
                st.error("This product has no recipe yet. Add it in the Recipe tab first.")
            else:
                need_ok = True
                need["Needed"] = need["qty_per_bundle"] * float(bundles)
                need["After"] = need["In stock"] - need["Needed"]
                st.markdown("**Raw materials this batch will use**")
                ui.table(ui.fmt(need[["Material", "Needed", "In stock", "After"]], ["Needed", "In stock", "After"]))
                if (need["After"] < 0).any():
                    st.warning("Some raw materials would go negative. You can still save if your recorded stock is out of date.")
        if st.button("Save production", type="primary", key="prd_save_" + str(n)):
            if not prod:
                st.error("Choose the product.")
            elif bundles <= 0:
                st.error("Enter the number of bundles.")
            elif not need_ok:
                st.error("This product has no recipe yet. Add it in the Recipe tab first.")
            else:
                try:
                    db.insert("production", {"production_date": pdt.isoformat(), "batch_ref": batch.strip() or None,
                                             "product_id": pid, "bundles": float(bundles), "notes": notes.strip() or None})
                    st.session_state["prd_n"] = n + 1
                    st.session_state["flash"] = "Production saved: " + ui.money(bundles) + " bundles of " + prod + "."
                    st.rerun()
                except Exception as ex:
                    st.error("Could not save: " + str(ex))
    prd = db.get("production", order="id", desc=True)
    st.markdown("#### Production history")
    if prd.empty:
        st.info("No production recorded yet.")
    else:
        h = prd.copy()
        h["Product"] = h["product_id"].map(pname)
        show = ui.fmt(h[["production_date", "batch_ref", "Product", "bundles", "notes"]], ["bundles"])
        show.columns = ["Date", "Batch", "Product", "Bundles", "Notes"]
        ui.table(show.head(200))
        ui.delete_entry("production", h, lambda r: str(r["production_date"]) + " · " + str(r["Product"]) + " · " + ui.money(r["bundles"]), "prd")

# --------------------------------------------------------------------- damages
with t_dam:
    n = st.session_state.setdefault("dam_n", 0)
    kind = st.radio("What was damaged?", ["Raw Material", "Finished Goods"], horizontal=True, key="dam_k_" + str(n))
    if kind == "Raw Material":
        src, label, cost_col = raw, "Raw material", "avg_cost"
    else:
        src, label, cost_col = fg, "Product", "std_cost"
    a, b, c = st.columns(3)
    ddate = a.date_input("Date", value=dt.date.today(), key="dam_d_" + str(n))
    names = src["name"].tolist() if not src.empty else []
    item = b.selectbox(label, names, index=None, placeholder="Choose", key="dam_i_" + kind.replace(" ", "") + str(n))
    dqty = c.number_input("Quantity", min_value=0.0, step=1.0, key="dam_q_" + str(n))
    e, f = st.columns(2)
    reason = e.selectbox("Reason", ["Breakage", "Leakage", "Defective / Expired", "Misprint / Label Fault",
                                    "Contamination", "Transit Damage", "Missing / Theft", "Other"], key="dam_r_" + str(n))
    notes = f.text_input("Notes (optional)", key="dam_n_" + str(n))
    unit_cost = 0.0
    if item:
        unit_cost = float(src.loc[src["name"] == item, cost_col].iloc[0])
        st.caption("Cost per unit: PKR " + ui.money(unit_cost, 2) + "   →   loss on this entry: PKR " + ui.money(unit_cost * dqty, 2))
    if st.button("Save damage", type="primary", key="dam_save_" + str(n)):
        if not item:
            st.error("Choose the item.")
        elif dqty <= 0:
            st.error("Enter a quantity.")
        else:
            try:
                row = {"damage_date": ddate.isoformat(), "damage_type": kind, "qty": float(dqty),
                       "reason": reason, "notes": notes.strip() or None, "unit_cost_at_time": unit_cost}
                row["raw_material_id"] = int(src.loc[src["name"] == item, "id"].iloc[0]) if kind == "Raw Material" else None
                row["product_id"] = int(src.loc[src["name"] == item, "id"].iloc[0]) if kind == "Finished Goods" else None
                db.insert("damages", row)
                st.session_state["dam_n"] = n + 1
                st.session_state["flash"] = "Damage recorded: " + ui.money(dqty) + " × " + item + "."
                st.rerun()
            except Exception as ex:
                st.error("Could not save: " + str(ex))
    dam = db.get("damages", order="id", desc=True)
    st.markdown("#### Damage history")
    if dam.empty:
        st.info("No damages recorded yet. Good news, or time to start recording.")
    else:
        h = dam.copy()
        h["Item"] = h.apply(lambda r: rname.get(r["raw_material_id"]) if r["damage_type"] == "Raw Material"
                            else pname.get(r["product_id"]), axis=1)
        h["Loss"] = h["qty"] * h["unit_cost_at_time"]
        st.metric("Total loss from damages", "PKR " + ui.money(h["Loss"].sum()))
        show = ui.fmt(h[["damage_date", "damage_type", "Item", "qty", "reason", "Loss"]], ["qty", "Loss"])
        show.columns = ["Date", "Type", "Item", "Quantity", "Reason", "Loss (PKR)"]
        ui.table(show.head(200))
        ui.delete_entry("damages", h, lambda r: str(r["damage_date"]) + " · " + str(r["Item"]) + " · " + ui.money(r["qty"]), "dam")
