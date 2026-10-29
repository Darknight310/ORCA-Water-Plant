import datetime as dt

import pandas as pd
import streamlit as st

import db
import ui

ui.header("Stock & Production", "Finished goods, raw materials, batches, recipes, production and damages")

products = db.get("products", order="id")
raw = db.get("v_raw_stock", order="id")
fg = db.get("v_product_stock", order="id")
recipe = db.get("recipe", order="id")
batches = db.get("raw_material_batches", order="batch_date")
prod_usage = db.get("production_batch_usage", order="id")

pname = db.name_map(products)
rname = db.name_map(raw)
REASONS = ["Breakage", "Leakage", "Defective / Expired", "Misprint / Label Fault",
           "Contamination", "Transit Damage", "Missing / Theft", "Other"]

section = ui.sections(["Finished Goods", "Raw Materials", "Batches", "Recipe", "Production", "Damages"], "stock_tab")


def settings_form(df, table_name, key, level_col, unit_label):
    """Physical count and alert level for one item (shown above the table)."""
    if df.empty:
        return
    with st.expander("Physical Count & Alert Level", expanded=True):
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

        v = fg.assign(margin=fg["avg_rate"] - fg["std_cost"]).sort_values("name")

        def show_details(r):
            st.caption("Cost per bundle = recipe × average raw material cost. "
                       "Status shows 'Set level' until you set an alert level.")

        ui.entity_table(
            "fg", v,
            [("Code", "code", None), ("Product", "name", None), ("Opening", "opening_stock", 0),
             ("Produced", "produced", 0), ("Sold", "sold", 0), ("Damaged", "damaged", 0),
             ("In Stock", "balance", 0), ("Cost / Bundle", "std_cost", 2), ("Avg Sell Rate", "avg_rate", 2),
             ("Margin / Bundle", "margin", 2), ("Stock Value", "stock_value", 0), ("Status", "status", None)],
            table="products",
            fields=[{"col": "name", "label": "Product Name", "required": True},
                    {"col": "code", "label": "Code", "required": True},
                    {"col": "min_stock", "label": "Alert Level (Min Stock, Bundles)", "kind": "num"}],
            label=lambda r: str(r["name"]),
            can_delete=lambda r: False)
        st.caption("Cost per bundle = recipe × average raw material cost. Status shows 'Set level' until you set an alert level. "
                   "Opening Stock can only be changed using Physical Count above, to keep it matching your real count.")

# ============================================================== RAW MATERIALS
elif section == "Raw Materials":
    if not raw.empty:
        k1, k2, k3 = st.columns(3)
        k1.metric("Raw Material Stock Value", "PKR " + ui.money(raw["stock_value"].sum()))
        k2.metric("Items", str(len(raw)))
        k3.metric("Items Running Low", str(int((raw["status"] == "LOW").sum())))
        settings_form(raw, "raw_materials", "raw", "reorder_level", "units")
        st.caption("Looking for individual purchase batches and FIFO costing? Check the **Batches** tab above.")
    with st.expander("Add A New Raw Material", expanded=True):
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

# ===================================================================== BATCHES
elif section == "Batches":
    st.caption("Every purchase becomes its own batch. Production and raw-material damages always use the "
               "oldest batch first (FIFO), and lock in that real cost permanently.")
    if batches.empty:
        st.info("No raw material batches yet. They're created automatically when you record a Purchase.")
    else:
        h = batches.copy()
        h["material"] = h["raw_material_id"].map(rname)
        h["value"] = h["qty_remaining"] * h["unit_cost"]
        h = h.sort_values(["material", "batch_date", "id"])

        k1, k2, k3 = st.columns(3)
        k1.metric("Total Batches", str(len(h)))
        k2.metric("Batches With Stock Left", str(int((h["qty_remaining"] > 0).sum())))
        k3.metric("Value Remaining In Batches", "PKR " + ui.money(h["value"].sum()))

        def replace_form(rec):
            st.markdown("**Replace This Batch (Same Price)**")
            st.caption("Use this when a supplier replaces damaged stock with new stock at the SAME original price. "
                       "This adds quantity to this exact batch — it does not create a new batch.")
            addq = st.number_input("Quantity Supplier Sent Back", min_value=0.0, step=1.0, key="rep_q_" + str(rec["id"]))
            if st.button("Add This Quantity", type="primary", key="rep_save_" + str(rec["id"])):
                if addq <= 0:
                    st.error("Enter a quantity.")
                else:
                    try:
                        db.replace_batch(rec["id"], addq)
                        st.session_state["flash"] = ("Added " + ui.money(addq) + " units back to this batch at PKR " +
                                                     ui.money(rec["unit_cost"], 2) + " each.")
                        st.rerun()
                    except Exception as ex:
                        st.error("Could not save: " + str(ex))

        ui.entity_table(
            "batch", h,
            [("Material", "material", None), ("Date", "batch_date", None), ("Source", "source", None),
             ("Reference", "ref", None), ("Qty In", "qty_in", 0), ("Unit Cost", "unit_cost", 2),
             ("Remaining", "qty_remaining", 0), ("Remaining Value", "value", 0)],
            detail=("Replace (Same Price)", replace_form),
            label=lambda r: str(r["material"]) + "  ·  " + str(r["batch_date"]),
            can_delete=lambda r: False)

# ==================================================================== RECIPE
elif section == "Recipe":
    st.caption("How much of each raw material goes into ONE bundle of each product. This drives production and product cost.")
    if not products.empty and not raw.empty:
        with st.expander("Add Or Change A Recipe Line", expanded=True):
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
                need_rows = recipe[recipe["product_id"] == pid]
                if need_rows.empty:
                    st.error("This product has no recipe yet. Add it in the Recipe section first.")
                else:
                    need_ok = True
                    preview, shortfall_any, total_cost_preview = [], False, 0.0
                    for _, rc in need_rows.iterrows():
                        rm_id = int(rc["raw_material_id"])
                        qty_needed = float(rc["qty_per_bundle"]) * float(bundles)
                        plan, shortfall = db.fifo_plan(rm_id, qty_needed)
                        mat = rname.get(rm_id, "?")
                        for p in plan:
                            preview.append({"Material": mat, "From Batch Dated": str(p["batch_date"]),
                                           "Quantity": p["qty"], "Unit Cost": p["unit_cost"], "Cost": p["qty"] * p["unit_cost"]})
                            total_cost_preview += p["qty"] * p["unit_cost"]
                        if shortfall > 1e-9:
                            shortfall_any = True
                            preview.append({"Material": mat, "From Batch Dated": "Not Enough Stock Recorded",
                                           "Quantity": shortfall, "Unit Cost": None, "Cost": None})
                    st.markdown("**Raw Materials This Batch Will Use (Oldest Stock First)**")
                    ui.table(ui.fmt(pd.DataFrame(preview), ["Quantity", "Unit Cost", "Cost"], 2))
                    st.caption("Estimated Production Cost: PKR " + ui.money(total_cost_preview, 2))
                    if shortfall_any:
                        st.warning("Some raw materials don't have enough batch stock on record. You can still save — "
                                  "a catch-up batch will be created automatically at the last known price.")
            if st.button("Save Production", type="primary", key="prd_save_" + str(n)):
                if not prod:
                    st.error("Choose the product.")
                elif bundles <= 0:
                    st.error("Enter the number of bundles.")
                elif not need_ok:
                    st.error("This product has no recipe yet. Add it in the Recipe section first.")
                else:
                    try:
                        _, total_cost = db.record_production(pdt.isoformat(), batch.strip() or None, pid, bundles,
                                                             notes.strip() or None, recipe)
                        st.session_state["prd_n"] = n + 1
                        st.session_state["flash"] = ("Production saved: " + ui.money(bundles) + " bundles of " + prod +
                                                     "  ·  Cost: PKR " + ui.money(total_cost, 2))
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
        h["_sort_date"] = pd.to_datetime(h["production_date"], errors="coerce")
        h = h.sort_values(["_sort_date", "id"], ascending=[False, False]).drop(columns="_sort_date").reset_index(drop=True)

        def show_prod_usage(r):
            u = prod_usage[prod_usage["production_id"] == r["id"]] if not prod_usage.empty else prod_usage
            if u is None or u.empty:
                st.caption("No raw material batch usage recorded for this entry.")
            else:
                uu = u.copy()
                uu["Material"] = uu["raw_material_id"].map(rname)
                uu["Cost"] = uu["qty_used"] * uu["unit_cost"]
                vv = uu[["Material", "batch_id", "qty_used", "unit_cost", "Cost"]].rename(
                    columns={"batch_id": "Batch ID", "qty_used": "Quantity Used", "unit_cost": "Unit Cost"})
                ui.table(ui.fmt(vv, ["Quantity Used", "Unit Cost", "Cost"], 2))
            left = float(r["qty_remaining"]) if pd.notna(r.get("qty_remaining")) else None
            if left is not None:
                st.caption("Bundles from this run still unsold / undamaged: " + ui.money(left))

        ui.entity_table(
            "prd", h,
            [("Date", "production_date", None), ("Batch", "batch_ref", None), ("Product", "product", None),
             ("Bundles", "bundles", 0), ("Cost", "total_cost", 2), ("Notes", "notes", None)],
            table="production",
            fields=[{"col": "batch_ref", "label": "Batch / Reference"},
                    {"col": "notes", "label": "Notes"}],
            detail=("Raw Materials Used", show_prod_usage),
            label=lambda r: str(r["production_date"]) + "  ·  " + str(r["product"]) + "  ·  " + ui.money(r["bundles"]),
            can_delete=lambda r: False)
        st.caption("Date, product and bundles can't be changed here, since the raw materials have already been "
                  "taken from specific batches, and sales now draw finished stock from this exact run. "
                  "If something was entered by mistake, let me know and we'll fix it directly.")

# =================================================================== DAMAGES
else:
    with st.expander("Record A Damage", expanded=True):
        n = st.session_state.setdefault("dam_n", 0)
        kind = st.radio("What Was Damaged?", ["Raw Material", "Finished Goods"], horizontal=True, key="dam_k_" + str(n))
        if kind == "Raw Material":
            src, label = raw, "Raw Material"
        else:
            src, label = fg, "Product"
        a, b, c = st.columns(3)
        ddate = a.date_input("Date", value=dt.date.today(), key="dam_d_" + str(n))
        names = src["name"].tolist() if not src.empty else []
        item = b.selectbox(label, names, index=None, placeholder="Choose", key="dam_i_" + kind.replace(" ", "") + str(n))
        dqty = c.number_input("Quantity", min_value=0.0, step=1.0, key="dam_q_" + str(n))
        e, f = st.columns(2)
        reason = e.selectbox("Reason", REASONS, key="dam_r_" + str(n))
        notes = f.text_input("Notes (Optional)", key="dam_n_" + str(n))

        item_id = None
        if item:
            item_id = int(src.loc[src["name"] == item, "id"].iloc[0])
            if kind == "Raw Material":
                if dqty > 0:
                    plan, shortfall = db.fifo_plan(item_id, dqty)
                    est = sum(p["qty"] * p["unit_cost"] for p in plan)
                    if shortfall > 1e-9:
                        fallback = plan[-1]["unit_cost"] if plan else float(src.loc[src["id"] == item_id, "avg_cost"].iloc[0])
                        est += shortfall * fallback
                        st.warning("Not enough batch stock recorded for this quantity — the extra amount will be "
                                  "added automatically as a catch-up batch at the last known price.")
                    st.caption("This will be taken from " + str(max(len(plan), 1)) + " batch(es), oldest first. "
                              "Estimated loss: PKR " + ui.money(est, 2))
            else:
                if dqty > 0:
                    plan, shortfall = db.fg_fifo_plan(item_id, dqty)
                    est = sum(p["qty"] * p["unit_cost"] for p in plan)
                    if shortfall > 1e-9:
                        if plan:
                            fallback = plan[-1]["unit_cost"]
                        else:
                            fallback = float(src.loc[src["id"] == item_id, "std_cost"].iloc[0])
                        est += shortfall * fallback
                        st.warning("Not enough finished-goods batch stock recorded for this quantity — the extra "
                                  "amount will be added automatically as a catch-up batch at the last known cost.")
                    st.caption("This will be taken from " + str(max(len(plan), 1)) + " production batch(es), oldest first. "
                              "Estimated loss: PKR " + ui.money(est, 2))

        if st.button("Save Damage", type="primary", key="dam_save_" + str(n)):
            if not item:
                st.error("Choose the item.")
            elif dqty <= 0:
                st.error("Enter a quantity.")
            else:
                try:
                    if kind == "Raw Material":
                        db.record_raw_damage(ddate.isoformat(), item_id, float(dqty), reason, notes.strip() or None)
                    else:
                        db.record_fg_damage(ddate.isoformat(), item_id, float(dqty), reason, notes.strip() or None)
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

        rm_dam = h[h["damage_type"] == "Raw Material"].copy()
        fg_dam = h[h["damage_type"] == "Finished Goods"].copy()

        st.markdown("**Raw Material Damages**")
        if rm_dam.empty:
            st.info("No raw material damages recorded yet.")
        else:
            def show_rm_batch(r):
                if pd.isna(r.get("batch_id")):
                    st.caption("No batch recorded for this entry.")
                    return
                b = batches[batches["id"] == r["batch_id"]]
                if b.empty:
                    st.caption("Batch not found (it may have been removed).")
                else:
                    bb = b.iloc[0]
                    st.caption("Taken From Batch Dated " + str(bb["batch_date"]) + "  ·  Cost At The Time: PKR " +
                              ui.money(bb["unit_cost"], 2) + " Per Unit")

            ui.entity_table(
                "dam_rm", rm_dam,
                [("Date", "damage_date", None), ("Item", "item", None), ("Quantity", "qty", 0),
                 ("Reason", "reason", None), ("Loss (PKR)", "loss", 0)],
                table="damages",
                fields=[{"col": "reason", "label": "Reason", "kind": "choice", "options": REASONS},
                        {"col": "notes", "label": "Notes"}],
                detail=("Which Batch Was Used", show_rm_batch),
                label=lambda r: str(r["damage_date"]) + "  ·  " + str(r["item"]) + "  ·  " + ui.money(r["qty"]),
                can_delete=lambda r: False)
            st.caption("Quantity and date can't be changed here, since the loss has already been taken from a "
                      "specific raw material batch. If this was entered by mistake, let me know and we'll fix it directly.")

        st.markdown("**Finished Goods Damages**")
        if fg_dam.empty:
            st.info("No finished goods damages recorded yet.")
        else:
            def show_fg_batch(r):
                if pd.isna(r.get("fg_batch_id")):
                    st.caption("No batch recorded for this entry.")
                    return
                p = db.get("production", order="id")
                b = p[p["id"] == r["fg_batch_id"]]
                if b.empty:
                    st.caption("Batch not found (it may have been removed).")
                else:
                    bb = b.iloc[0]
                    unit_cost = float(bb["total_cost"] or 0) / float(bb["bundles"] or 1)
                    st.caption("Taken From Production Batch Dated " + str(bb["production_date"]) + "  ·  Batch Ref: " +
                              str(bb["batch_ref"] or "—") + "  ·  Cost At The Time: PKR " +
                              ui.money(unit_cost, 2) + " Per Bundle")

            ui.entity_table(
                "dam_fg", fg_dam,
                [("Date", "damage_date", None), ("Item", "item", None), ("Quantity", "qty", 0),
                 ("Reason", "reason", None), ("Loss (PKR)", "loss", 0)],
                table="damages",
                fields=[{"col": "reason", "label": "Reason", "kind": "choice", "options": REASONS},
                        {"col": "notes", "label": "Notes"}],
                detail=("Which Batch Was Used", show_fg_batch),
                label=lambda r: str(r["damage_date"]) + "  ·  " + str(r["item"]) + "  ·  " + ui.money(r["qty"]),
                can_delete=lambda r: False)
            st.caption("Quantity and date can't be changed here, since the loss has already been taken from a "
                      "specific finished-goods batch. If this was entered by mistake, let me know and we'll fix it directly.")
