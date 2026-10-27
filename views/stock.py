import datetime as dt

import pandas as pd
import streamlit as st

import db
import ui

ui.header("Stock & Production", "Finished goods, raw materials, recipes, purchases, production and damages")

products = db.get("products", order="id")
raw = db.get("v_raw_stock", order="id")
fg = db.get("v_product_stock", order="id")
recipe = db.get("recipe", order="id")
try:
    suppliers = db.get("suppliers", order="name")
except Exception:
    suppliers = None

pname = db.name_map(products)
rname = db.name_map(raw)
REASONS = ["Breakage", "Leakage", "Defective / Expired", "Misprint / Label Fault",
           "Contamination", "Transit Damage", "Missing / Theft", "Other"]

section = ui.sections(["Finished Goods", "Raw Materials", "Recipe", "Purchases", "Production", "Damages"], "stock_tab")


def settings_form(df, table_name, key, level_col, unit_label):
    """Physical count and alert level for one item (shown above the table)."""
    if df.empty:
        return
    with st.expander("Physical Count & Alert Level"):
        st.caption("Enter what you actually counted. The app adjusts the starting stock so the balance matches your count.")
        name = st.selectbox("Item", df["name"].tolist(), index=None, placeholder="Choose An Item", key="set_item_" + key)
        if name:
            r = df[df["name"] == name].iloc[0]
            rid = int(r["id"])
            cur = 0.0 if pd.isna(r[level_col]) else float(r[level_col])
            a, b = st.columns(2)
            count = a.number_input("Counted Quantity (" + unit_label + ")", min_value=0.0, value=float(r["balance"]),
                                   step=1.0, key="set_cnt_" + key + str(rid))
            level = b.number_input("Alert Me When Stock Falls To (" + unit_label + ")", min_value=0.0, value=cur,
                                   step=1.0, key="set_lvl_" + key + str(rid))
            if st.button("Save", type="primary", key="set_save_" + key + str(rid)):
                new_open = float(count) - (float(r["balance"]) - float(r["opening_stock"]))
                try:
                    db.update(table_name, rid, {"opening_stock": new_open, level_col: float(level)})
                    st.session_state["flash"] = name + " updated."
                    st.rerun()
                except Exception as e:
                    st.error("Could not save: " + str(e))


# ============================================================= FINISHED GOODS
if section == "Finished Goods":
    if fg.empty:
        st.info("No products yet.")
    else:
        k1, k2, k3 = st.columns(3)
        k1.metric("Finished Goods Stock Value", "PKR " + ui.money(fg["stock_value"].sum()))
        k2.metric("Bundles In Stock", ui.money(fg["balance"].sum()))
        k3.metric("Products Running Low", str(int((fg["status"] == "LOW").sum())))
        settings_form(fg, "products", "fg", "min_stock", "bundles")
        v = fg.assign(margin=fg["avg_rate"] - fg["std_cost"])
        v = v[["name", "opening_stock", "produced", "sold", "damaged", "balance", "std_cost", "avg_rate",
               "margin", "stock_value", "status"]]
        v = ui.fmt(v, ["opening_stock", "produced", "sold", "damaged", "balance", "stock_value"])
        v = ui.fmt(v, ["std_cost", "avg_rate", "margin"], 2)
        v.columns = ["Product", "Opening", "Produced", "Sold", "Damaged", "In Stock", "Cost / Bundle",
                     "Avg Sell Rate", "Margin / Bundle", "Stock Value", "Status"]
        ui.table(v)
        st.caption("Cost per bundle = recipe × average raw material cost. Status shows 'Set level' until you set an alert level.")

# ============================================================== RAW MATERIALS
elif section == "Raw Materials":
    if not raw.empty:
        k1, k2, k3 = st.columns(3)
        k1.metric("Raw Material Stock Value", "PKR " + ui.money(raw["stock_value"].sum()))
        k2.metric("Items", str(len(raw)))
        k3.metric("Items Running Low", str(int((raw["status"] == "LOW").sum())))
        settings_form(raw, "raw_materials", "raw", "reorder_level", "units")
    with st.expander("Add A New Raw Material"):
        n = st.session_state.setdefault("rm_n", 0)
        a, b, c = st.columns(3)
        nm = a.text_input("Name", key="rm_name_" + str(n))
        unit = b.text_input("Unit", value="Pcs", key="rm_unit_" + str(n))
        code = c.text_input("Code", value=db.next_code(raw["code"].tolist() if not raw.empty else [], "RM-"),
                            key="rm_code_" + str(n))
        d, e = st.columns(2)
        oq = d.number_input("Quantity You Have Now", min_value=0.0, step=1.0, key="rm_oq_" + str(n))
        oc = e.number_input("Cost Per Unit (PKR)", min_value=0.0, step=0.1, format="%.2f", key="rm_oc_" + str(n))
        st.caption("After adding it, put it into a product's recipe in the Recipe section.")
        if st.button("Add Raw Material", type="primary", key="rm_save_" + str(n)):
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
    if raw.empty:
        st.info("No raw materials yet.")
    else:
        v = raw[["name", "unit", "opening_stock", "purchased_qty", "used_qty", "damaged_qty", "balance",
                 "avg_cost", "stock_value", "reorder_level", "status"]]
        v = ui.fmt(v, ["opening_stock", "purchased_qty", "used_qty", "damaged_qty", "balance", "stock_value", "reorder_level"])
        v = ui.fmt(v, ["avg_cost"], 2)
        v.columns = ["Raw Material", "Unit", "Opening", "Purchased", "Used", "Damaged", "In Stock",
                     "Avg Cost", "Stock Value", "Alert Level", "Status"]
        ui.table(v)

# ==================================================================== RECIPE
elif section == "Recipe":
    st.caption("How much of each raw material goes into ONE bundle of each product. This drives production and product cost.")
    if not products.empty and not raw.empty:
        with st.expander("Add Or Change A Recipe Line"):
            a, b, c = st.columns(3)
            rp = a.selectbox("Product", products["name"].tolist(), index=None, placeholder="Choose", key="rec_p")
            rm = b.selectbox("Raw Material", raw["name"].tolist(), index=None, placeholder="Choose", key="rec_m")
            rq = c.number_input("Quantity Per Bundle", min_value=0.0, step=1.0, key="rec_q")
            st.caption("Saving a quantity replaces the old one. Use 0 to remove a material from a recipe.")
            if st.button("Save Recipe Line", type="primary", key="rec_save"):
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
    if recipe.empty:
        st.info("No recipe lines yet.")
    else:
        rc = recipe.assign(Product=recipe["product_id"].map(pname), Material=recipe["raw_material_id"].map(rname))
        pv = rc.pivot_table(index="Material", columns="Product", values="qty_per_bundle", aggfunc="sum").fillna(0)
        pv = pv.reset_index()
        ui.table(ui.fmt(pv, [c for c in pv.columns if c != "Material"], 0))

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
            total = float(qty) * float(cost)
            rs = db.reinvest()
            from_sales, from_profit = 0.0, 0.0
            if rs["enabled"]:
                src_choice = st.radio("Money Used For This Purchase", ["Sales Money", "Current Profit", "Both"],
                                      horizontal=True, key="pur_src_" + str(n))
                if src_choice == "Sales Money":
                    from_sales, from_profit = total, 0.0
                elif src_choice == "Current Profit":
                    from_sales, from_profit = 0.0, total
                else:
                    from_sales = st.number_input("Part Paid From Sales Money (PKR)", min_value=0.0, step=100.0,
                                                 key="pur_fs_" + str(n))
                    from_profit = total - float(from_sales)
                    st.caption("The rest, PKR " + ui.money(from_profit, 2) + ", is paid from Current Profit.")
                st.caption("Sales money still to reinvest: PKR " + ui.money(rs["left_to_reinvest"]) +
                           "   ·   Profit in hand: PKR " + ui.money(rs["profit_in_hand"]))
                if from_sales > max(rs["left_to_reinvest"], 0) + 0.5:
                    st.warning("This is more than the sales money still waiting to be reinvested.")
                if from_profit > max(rs["profit_in_hand"], 0) + 0.5:
                    st.warning("This is more than the profit you have in hand.")
            else:
                st.info("To record where the money comes from, run orca_update_2.sql in Supabase first.")
            if item:
                r = raw[raw["name"] == item].iloc[0]
                old_q = float(r["opening_stock"]) + float(r["purchased_qty"])
                old_v = float(r["opening_stock"]) * float(r["opening_unit_cost"]) + float(r["purchase_value"])
                new_q = old_q + float(qty)
                new_avg = (old_v + float(qty) * float(cost)) / new_q if new_q else 0
                st.caption("Total this purchase: PKR " + ui.money(total, 2) + "   ·   Average cost now: " +
                           ui.money(r["avg_cost"], 2) + "  →  after this purchase: " + ui.money(new_avg, 2))
            if st.button("Save Purchase", type="primary", key="pur_save_" + str(n)):
                supplier = sup_new.strip() or sup_pick or None
                if not item:
                    st.error("Choose a raw material.")
                elif qty <= 0:
                    st.error("Enter a quantity.")
                elif rs["enabled"] and from_sales > total + 0.01:
                    st.error("The part paid from sales money cannot be more than the purchase total.")
                else:
                    try:
                        rid = int(raw.loc[raw["name"] == item, "id"].iloc[0])
                        row = {"purchase_date": pdate.isoformat(), "supplier": supplier,
                               "raw_material_id": rid, "qty": float(qty), "unit_cost": float(cost),
                               "ref": ref.strip() or None, "notes": notes.strip() or None}
                        if rs["enabled"]:
                            row["paid_from_sales"] = round(float(from_sales), 2)
                            row["paid_from_profit"] = round(float(from_profit), 2)
                        db.insert("purchases", row)
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
        split = "paid_from_sales" in h.columns
        cols = [("Date", "purchase_date", None), ("Supplier", "supplier", None), ("Raw Material", "material", None),
                ("Quantity", "qty", 0), ("Unit Cost", "unit_cost", 2), ("Total", "total", 0)]
        fields = [{"col": "purchase_date", "label": "Date", "kind": "date"},
                  {"col": "supplier", "label": "Supplier"},
                  {"col": "raw_material_id", "label": "Raw Material", "kind": "select", "options": rname},
                  {"col": "qty", "label": "Quantity", "kind": "num"},
                  {"col": "unit_cost", "label": "Unit Cost (PKR)", "kind": "num", "step": 0.1},
                  {"col": "ref", "label": "Invoice / Reference"},
                  {"col": "notes", "label": "Notes"}]
        if split:
            cols += [("From Sales Money", "paid_from_sales", 0), ("From Current Profit", "paid_from_profit", 0)]
            fields += [{"col": "paid_from_sales", "label": "Paid From Sales Money (PKR)", "kind": "num", "step": 100.0},
                       {"col": "paid_from_profit", "label": "Paid From Current Profit (PKR)", "kind": "num", "step": 100.0}]
        cols.append(("Reference", "ref", None))

        def check_purchase(payload, rec):
            if split:
                tot = payload["qty"] * payload["unit_cost"]
                paid = payload["paid_from_sales"] + payload["paid_from_profit"]
                if paid > 0 and abs(tot - paid) > 0.5:
                    return "The two paid-from amounts must add up to the purchase total (PKR " + ui.money(tot, 2) + ")."
            return None

        ui.entity_table(
            "pur", h, cols, table="purchases", fields=fields, validate=check_purchase,
            label=lambda r: str(r["purchase_date"]) + "  ·  " + str(r["material"]) + "  ·  " + ui.money(r["qty"]))

# ================================================================= PRODUCTION
elif section == "Production":
    if products.empty:
        st.info("No products yet.")
    else:
        with st.expander("Record Production", expanded=True):
            n = st.session_state.setdefault("prd_n", 0)
            a, b, c = st.columns(3)
            pdt = a.date_input("Date", value=dt.date.today(), key="prd_d_" + str(n))
            batch = b.text_input("Batch / Reference", key="prd_b_" + str(n))
            prod = c.selectbox("Product Made", products["name"].tolist(), index=None, placeholder="Choose", key="prd_p_" + str(n))
            d, e = st.columns([1, 2])
            bundles = d.number_input("Bundles Produced", min_value=0.0, step=1.0, key="prd_q_" + str(n))
            notes = e.text_input("Notes (Optional)", key="prd_n_" + str(n))
            need_ok = False
            pid = None
            if prod and bundles > 0:
                pid = int(products.loc[products["name"] == prod, "id"].iloc[0])
                rs = raw[["id", "name", "unit", "balance"]].rename(columns={"id": "rm_id", "name": "Material", "balance": "In Stock"})
                need = recipe[recipe["product_id"] == pid].merge(rs, left_on="raw_material_id", right_on="rm_id")
                if need.empty:
                    st.error("This product has no recipe yet. Add it in the Recipe section first.")
                else:
                    need_ok = True
                    need["Needed"] = need["qty_per_bundle"] * float(bundles)
                    need["After"] = need["In Stock"] - need["Needed"]
                    st.markdown("**Raw Materials This Batch Will Use**")
                    ui.table(ui.fmt(need[["Material", "Needed", "In Stock", "After"]], ["Needed", "In Stock", "After"]))
                    if (need["After"] < 0).any():
                        st.warning("Some raw materials would go negative. You can still save if your recorded stock is out of date.")
            if st.button("Save Production", type="primary", key="prd_save_" + str(n)):
                if not prod:
                    st.error("Choose the product.")
                elif bundles <= 0:
                    st.error("Enter the number of bundles.")
                elif not need_ok:
                    st.error("This product has no recipe yet. Add it in the Recipe section first.")
                else:
                    try:
                        db.insert("production", {"production_date": pdt.isoformat(), "batch_ref": batch.strip() or None,
                                                 "product_id": pid, "bundles": float(bundles), "notes": notes.strip() or None})
                        st.session_state["prd_n"] = n + 1
                        st.session_state["flash"] = "Production saved: " + ui.money(bundles) + " bundles of " + prod + "."
                        st.rerun()
                    except Exception as ex:
                        st.error("Could not save: " + str(ex))
    st.markdown("#### Production History")
    prd = db.get("production", order="id", desc=True)
    if prd.empty:
        st.info("No production recorded yet.")
    else:
        h = prd.copy()
        h["product"] = h["product_id"].map(pname)
        ui.entity_table(
            "prd", h,
            [("Date", "production_date", None), ("Batch", "batch_ref", None), ("Product", "product", None),
             ("Bundles", "bundles", 0), ("Notes", "notes", None)],
            table="production",
            fields=[{"col": "production_date", "label": "Date", "kind": "date"},
                    {"col": "batch_ref", "label": "Batch / Reference"},
                    {"col": "product_id", "label": "Product", "kind": "select", "options": pname},
                    {"col": "bundles", "label": "Bundles Produced", "kind": "num"},
                    {"col": "notes", "label": "Notes"}],
            label=lambda r: str(r["production_date"]) + "  ·  " + str(r["product"]) + "  ·  " + ui.money(r["bundles"]))

# =================================================================== DAMAGES
else:
    with st.expander("Record A Damage", expanded=True):
        n = st.session_state.setdefault("dam_n", 0)
        kind = st.radio("What Was Damaged?", ["Raw Material", "Finished Goods"], horizontal=True, key="dam_k_" + str(n))
        if kind == "Raw Material":
            src, label, cost_col = raw, "Raw Material", "avg_cost"
        else:
            src, label, cost_col = fg, "Product", "std_cost"
        a, b, c = st.columns(3)
        ddate = a.date_input("Date", value=dt.date.today(), key="dam_d_" + str(n))
        names = src["name"].tolist() if not src.empty else []
        item = b.selectbox(label, names, index=None, placeholder="Choose", key="dam_i_" + kind.replace(" ", "") + str(n))
        dqty = c.number_input("Quantity", min_value=0.0, step=1.0, key="dam_q_" + str(n))
        e, f = st.columns(2)
        reason = e.selectbox("Reason", REASONS, key="dam_r_" + str(n))
        notes = f.text_input("Notes (Optional)", key="dam_n_" + str(n))
        unit_cost = 0.0
        if item:
            unit_cost = float(src.loc[src["name"] == item, cost_col].iloc[0])
            st.caption("Cost per unit: PKR " + ui.money(unit_cost, 2) + "   →   loss on this entry: PKR " + ui.money(unit_cost * dqty, 2))
        if st.button("Save Damage", type="primary", key="dam_save_" + str(n)):
            if not item:
                st.error("Choose the item.")
            elif dqty <= 0:
                st.error("Enter a quantity.")
            else:
                try:
                    row = {"damage_date": ddate.isoformat(), "damage_type": kind, "qty": float(dqty),
                           "reason": reason, "notes": notes.strip() or None, "unit_cost_at_time": unit_cost}
                    iid = int(src.loc[src["name"] == item, "id"].iloc[0])
                    row["raw_material_id"] = iid if kind == "Raw Material" else None
                    row["product_id"] = iid if kind == "Finished Goods" else None
                    db.insert("damages", row)
                    st.session_state["dam_n"] = n + 1
                    st.session_state["flash"] = "Damage recorded: " + ui.money(dqty) + " × " + item + "."
                    st.rerun()
                except Exception as ex:
                    st.error("Could not save: " + str(ex))
    st.markdown("#### Damage History")
    dam = db.get("damages", order="id", desc=True)
    if dam.empty:
        st.info("No damages recorded yet.")
    else:
        h = dam.copy()
        h["item"] = h.apply(lambda r: rname.get(r["raw_material_id"]) if r["damage_type"] == "Raw Material"
                            else pname.get(r["product_id"]), axis=1)
        h["loss"] = h["qty"] * h["unit_cost_at_time"]
        st.metric("Total Loss From Damages", "PKR " + ui.money(h["loss"].sum()))
        ui.entity_table(
            "dam", h,
            [("Date", "damage_date", None), ("Type", "damage_type", None), ("Item", "item", None),
             ("Quantity", "qty", 0), ("Reason", "reason", None), ("Loss (PKR)", "loss", 0)],
            table="damages",
            fields=[{"col": "damage_date", "label": "Date", "kind": "date"},
                    {"col": "qty", "label": "Quantity", "kind": "num"},
                    {"col": "reason", "label": "Reason", "kind": "choice", "options": REASONS},
                    {"col": "notes", "label": "Notes"}],
            label=lambda r: str(r["damage_date"]) + "  ·  " + str(r["item"]) + "  ·  " + ui.money(r["qty"]))
