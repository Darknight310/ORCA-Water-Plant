import datetime as dt
import io
import re

import pandas as pd
import streamlit as st

PAGE = 1000
METHODS = ["Cash", "Bank Transfer", "Easypaisa / JazzCash", "Cheque", "Other"]
EXPORT_SHEETS = ["customers", "products", "raw_materials", "recipe", "invoices", "invoice_lines",
                 "payments", "purchases", "production", "damages", "expenses",
                 "v_invoice_summary", "v_raw_stock", "v_product_stock", "v_pnl",
                 "v_product_cost", "v_sale_order_summary"]
OPTIONAL_SHEETS = ["suppliers", "sale_orders", "sale_order_lines", "raw_material_batches",
                   "production_batch_usage", "sale_batch_usage", "damage_batch_usage",
                   "supplier_payments"]


def _supabase_key():
    # Preferred name is SUPABASE_SERVICE_KEY; SUPABASE_KEY kept for older deployments.
    return st.secrets.get("SUPABASE_SERVICE_KEY") or st.secrets["SUPABASE_KEY"]


@st.cache_resource
def _client():
    from supabase import create_client
    return create_client(st.secrets["SUPABASE_URL"], _supabase_key())


@st.cache_data(ttl=15, show_spinner=False)
def get(table, order=None, desc=False):
    """Read a whole table or view (handles Supabase's 1000-row page limit)."""
    rows, start = [], 0
    while True:
        q = _client().table(table).select("*")
        if order:
            q = q.order(order, desc=desc)
        batch = q.range(start, start + PAGE - 1).execute().data
        rows += batch
        if len(batch) < PAGE:
            break
        start += PAGE
    return pd.DataFrame(rows)


def insert(table, data):
    res = _client().table(table).insert(data).execute()
    st.cache_data.clear()
    return res.data


def update(table, id_, data):
    _client().table(table).update(data).eq("id", int(id_)).execute()
    st.cache_data.clear()


def upsert(table, data, on_conflict):
    _client().table(table).upsert(data, on_conflict=on_conflict).execute()
    st.cache_data.clear()


def delete(table, id_):
    _client().table(table).delete().eq("id", int(id_)).execute()
    st.cache_data.clear()


def update_where(table, col, val, data):
    _client().table(table).update(data).eq(col, val).execute()
    st.cache_data.clear()


def delete_where(table, col, val):
    _client().table(table).delete().eq(col, val).execute()
    st.cache_data.clear()


def delete_ids(table, ids):
    if ids:
        _client().table(table).delete().in_("id", [int(i) for i in ids]).execute()
        st.cache_data.clear()


def _one(table, id_):
    """Fetch one fresh row by ID (not the 15-second cached whole-table read)."""
    rows = _client().table(table).select("*").eq("id", int(id_)).limit(1).execute().data
    return rows[0] if rows else None


def _num(v, default=0.0):
    try:
        if v is None or pd.isna(v):
            return float(default)
        return float(v)
    except (TypeError, ValueError):
        return float(default)


def _close(a, b, tol=1e-9):
    return abs(_num(a) - _num(b)) <= tol


def _records(rows):
    if rows is None:
        return []
    if isinstance(rows, pd.DataFrame):
        return rows.to_dict("records")
    return list(rows)


def _adjust_raw_batch_remaining(batch_id, delta):
    row = _one("raw_material_batches", batch_id)
    if not row:
        raise ValueError("A raw-material batch linked to this entry could not be found.")
    new_remaining = _num(row.get("qty_remaining")) + float(delta)
    if new_remaining < -1e-9:
        raise ValueError("That correction would make a raw-material batch go below zero.")
    update("raw_material_batches", batch_id, {"qty_remaining": max(new_remaining, 0.0)})
    return max(new_remaining, 0.0)


def _adjust_fg_batch_remaining(production_id, delta):
    row = _one("production", production_id)
    if not row:
        raise ValueError("A production batch linked to this entry could not be found.")
    new_remaining = _num(row.get("qty_remaining")) + float(delta)
    if new_remaining < -1e-9:
        raise ValueError("That correction would make a finished-goods batch go below zero.")
    update("production", production_id, {"qty_remaining": max(new_remaining, 0.0)})
    return max(new_remaining, 0.0)


def _restore_raw_usage(rows):
    for r in _records(rows):
        if r.get("batch_id") is not None and not pd.isna(r.get("batch_id")):
            _adjust_raw_batch_remaining(int(r["batch_id"]), _num(r.get("qty_used")))


def _take_exact_raw_usage(rows):
    for r in _records(rows):
        if r.get("batch_id") is not None and not pd.isna(r.get("batch_id")):
            _adjust_raw_batch_remaining(int(r["batch_id"]), -_num(r.get("qty_used")))


def _restore_fg_usage(rows):
    for r in _records(rows):
        pid = r.get("production_id")
        if pid is not None and not pd.isna(pid):
            _adjust_fg_batch_remaining(int(pid), _num(r.get("qty_used")))


def _take_exact_fg_usage(rows):
    for r in _records(rows):
        pid = r.get("production_id")
        if pid is not None and not pd.isna(pid):
            _adjust_fg_batch_remaining(int(pid), -_num(r.get("qty_used")))


@st.cache_data(ttl=60, show_spinner=False)
def has_split():
    """True once orca_update_2.sql has been run (purchases know where the money came from)."""
    try:
        _client().table("purchases").select("paid_from_sales").limit(1).execute()
        return True
    except Exception:
        return False


def reinvest():
    """How much sales money and profit money has gone back into raw materials - counting
    both purchases paid at the time, and later Supplier Payments against credit purchases."""
    pnl = get("v_pnl")
    pur = get("purchases", order="id")
    pay = get("supplier_payments", order="id")
    cogs = float(pnl.iloc[0]["cogs"]) if not pnl.empty else 0.0
    current = float(pnl.iloc[0]["net_retained_profit"]) if not pnl.empty else 0.0
    from_sales = from_profit = 0.0
    if not pur.empty and "paid_from_sales" in pur.columns:
        from_sales += float(pur["paid_from_sales"].fillna(0).sum())
        from_profit += float(pur["paid_from_profit"].fillna(0).sum())
    if pay is not None and not pay.empty:
        from_sales += float(pay["paid_from_sales"].fillna(0).sum())
        from_profit += float(pay["paid_from_profit"].fillna(0).sum())
    return {"enabled": has_split(), "cogs": cogs, "current_profit": current,
            "from_sales": from_sales, "from_profit": from_profit,
            "left_to_reinvest": cogs - from_sales, "profit_in_hand": current - from_profit}


def cash_in_hand():
    """How much real cash is sitting in hand / bank right now - separate from Profit & Loss.
    Buying raw materials drops this immediately (unlike Profit, which only drops at sale time)."""
    summ = get("v_invoice_summary", order="id")
    received = float(summ["received"].sum()) if not summ.empty else 0.0

    pur = get("purchases", order="id")
    paid_suppliers = 0.0
    if not pur.empty:
        total = pur["qty"] * pur["unit_cost"]
        paid = pur["paid_amount"].fillna(total) if "paid_amount" in pur.columns else total
        paid_suppliers += float(paid.sum())
    sp = get("supplier_payments", order="id")
    if sp is not None and not sp.empty:
        paid_suppliers += float(sp["amount"].sum())

    pnl = get("v_pnl")
    op_exp = float(pnl.iloc[0]["operating_expenses"]) if not pnl.empty else 0.0
    draws = float(pnl.iloc[0]["owner_draws"]) if not pnl.empty else 0.0

    cash = received - paid_suppliers - op_exp - draws
    return {"received": received, "paid_suppliers": paid_suppliers,
            "operating_expenses": op_exp, "owner_draws": draws, "cash_in_hand": cash}


def name_map(df, key="name"):
    if df is None or df.empty:
        return {}
    return dict(zip(df["id"], df[key]))


def _numbers(values):
    return [int(d) for d in (re.sub(r"\D", "", str(v)) for v in values) if d]


def next_no(values, prefix):
    return prefix + str(max(_numbers(values), default=0) + 1)


def next_code(values, prefix, width=2):
    return prefix + str(max(_numbers(values), default=0) + 1).zfill(width)


def export_all():
    """Every table in one Excel file, for your own backup."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for t in EXPORT_SHEETS + OPTIONAL_SHEETS:
            try:
                df = get(t, order="id")
            except Exception:
                continue
            df.to_excel(xw, sheet_name=t[:31], index=False)
    return buf.getvalue()


# ============================================================= BATCH COSTING
def get_batches(raw_material_id, only_available=True):
    """All batches for one raw material, oldest first."""
    df = get("raw_material_batches", order="batch_date")
    if df.empty:
        return df
    df = df[df["raw_material_id"] == int(raw_material_id)]
    if only_available:
        df = df[df["qty_remaining"] > 0]
    return df.sort_values(["batch_date", "id"]).reset_index(drop=True)


def fifo_plan(raw_material_id, qty_needed):
    """PREVIEW ONLY - changes nothing. Returns (plan, shortfall).
    plan is a list of {batch_id, batch_date, qty, unit_cost}, oldest batch first."""
    qty_needed = float(qty_needed)
    plan, remaining = [], qty_needed
    for _, b in get_batches(raw_material_id).iterrows():
        if remaining <= 1e-9:
            break
        take = min(float(b["qty_remaining"]), remaining)
        if take <= 0:
            continue
        plan.append({"batch_id": int(b["id"]), "batch_date": b["batch_date"],
                     "qty": take, "unit_cost": float(b["unit_cost"])})
        remaining -= take
    return plan, max(remaining, 0.0)


def consume_fifo(raw_material_id, qty_needed):
    """Actually takes stock out of the oldest batch(es) first. If there isn't enough
    recorded batch stock, NOTHING is changed and a clear error is raised - stock is
    never invented. Record the missing purchase / opening batch first, then retry.
    Returns the plan that was actually used."""
    raw_material_id = int(raw_material_id)
    qty_needed = float(qty_needed)
    all_batches = get_batches(raw_material_id, only_available=False)
    avail = all_batches[all_batches["qty_remaining"] > 0] if not all_batches.empty else all_batches
    plan, updates, remaining = [], [], qty_needed
    for _, b in avail.iterrows():
        if remaining <= 1e-9:
            break
        take = min(float(b["qty_remaining"]), remaining)
        if take <= 0:
            continue
        plan.append({"batch_id": int(b["id"]), "batch_date": b["batch_date"],
                     "qty": take, "unit_cost": float(b["unit_cost"])})
        updates.append((int(b["id"]), float(b["qty_remaining"]) - take))
        remaining -= take
    if remaining > 1e-9:
        raise ValueError("Not enough recorded raw-material batch stock (material ID "
                         + str(raw_material_id) + "): short by " + format(remaining, "g")
                         + ". Nothing was saved. Record the missing purchase or opening "
                         "batch first, then try again.")
    for bid, new_rem in updates:
        _client().table("raw_material_batches").update({"qty_remaining": new_rem}).eq("id", bid).execute()
    st.cache_data.clear()
    return plan


def replace_batch(batch_id, qty_add):
    """Supplier sent replacement stock at the SAME price - tops up this exact batch
    instead of creating a new one."""
    row = _client().table("raw_material_batches").select("*").eq("id", int(batch_id)).limit(1).execute().data
    if not row:
        raise Exception("Batch not found.")
    row = row[0]
    update("raw_material_batches", batch_id, {
        "qty_in": float(row["qty_in"]) + float(qty_add),
        "qty_remaining": float(row["qty_remaining"]) + float(qty_add)})


def _purchase_for_batch(batch_id):
    purchases = get("purchases", order="id")
    if purchases.empty or "batch_id" not in purchases.columns:
        return None
    mine = purchases[purchases["batch_id"] == int(batch_id)]
    return mine.iloc[0].to_dict() if not mine.empty else None


def update_raw_batch(batch_id, raw_material_id, batch_date, source, ref, qty_in, unit_cost, qty_remaining):
    """Correct one raw-material batch.

    If the batch came from a Purchase, the matching purchase line is kept in
    sync for date/material/quantity/cost/reference. The corrected quantity in
    minus remaining can never be less than what production/damage records say
    already came out of this batch.
    """
    batch_id = int(batch_id)
    raw_material_id = int(raw_material_id)
    qty_in = float(qty_in)
    unit_cost = float(unit_cost)
    qty_remaining = float(qty_remaining)
    if qty_in < 0 or qty_remaining < 0 or unit_cost < 0:
        raise ValueError("Batch quantities and cost cannot be negative.")
    if qty_remaining > qty_in + 1e-9:
        raise ValueError("Quantity Remaining cannot be more than Quantity In.")
    old = _one("raw_material_batches", batch_id)
    if not old:
        raise ValueError("That batch could not be found.")
    recorded = _raw_batch_recorded_usage(batch_id)
    if qty_in - qty_remaining + 1e-9 < recorded:
        raise ValueError("Those quantities would say only %.10g came out of this batch, but "
                         "production/damage records already used %.10g. Correct those entries first."
                         % (max(qty_in - qty_remaining, 0.0), recorded))
    if int(_num(old.get("raw_material_id"))) != raw_material_id and recorded > 1e-9:
        raise ValueError("The material cannot be changed after this batch has been used. "
                         "Correct the production/damage entries that used it first.")

    payload = {
        "raw_material_id": raw_material_id, "batch_date": batch_date,
        "source": (source or "").strip() or "Other", "ref": (ref or "").strip() or None,
        "qty_in": qty_in, "unit_cost": unit_cost, "qty_remaining": qty_remaining,
    }
    purchase = _purchase_for_batch(batch_id)
    purchase_payload = None
    if purchase:
        stock_fields_changed = (
            int(_num(old.get("raw_material_id"))) != raw_material_id
            or str(old.get("batch_date")) != str(batch_date)
            or (old.get("ref") or None) != payload["ref"]
            or not _close(old.get("qty_in"), qty_in)
            or not _close(old.get("unit_cost"), unit_cost)
        )
        if stock_fields_changed:
            old_total = _num(purchase.get("qty")) * _num(purchase.get("unit_cost"))
            paid = _num(purchase.get("paid_amount"), old_total)
            if paid > qty_in * unit_cost + 0.01:
                raise ValueError("This batch came from a purchase whose Paid Amount is now higher "
                                 "than the corrected purchase total. Edit that purchase's payment "
                                 "amount in Suppliers & Purchases → Purchases first.")
            purchase_payload = {
                "purchase_date": batch_date, "raw_material_id": raw_material_id,
                "qty": qty_in, "unit_cost": unit_cost, "ref": payload["ref"],
            }
    old_payload = {k: old.get(k) for k in payload}
    update("raw_material_batches", batch_id, payload)
    if purchase_payload:
        try:
            update("purchases", int(purchase["id"]), purchase_payload)
        except Exception:
            update("raw_material_batches", batch_id, old_payload)
            raise


def delete_raw_batch(batch_id):
    """Delete a completely unused non-purchase batch."""
    batch_id = int(batch_id)
    old = _one("raw_material_batches", batch_id)
    if not old:
        raise ValueError("That batch could not be found.")
    if _purchase_for_batch(batch_id):
        raise ValueError("This batch belongs to a purchase. Delete it from Suppliers & Purchases "
                         "→ Purchases so the purchase line and its batch are removed together.")
    recorded = _raw_batch_recorded_usage(batch_id)
    consumed = _num(old.get("qty_in")) - _num(old.get("qty_remaining"))
    if recorded > 1e-9 or consumed > 1e-9:
        raise ValueError("This batch cannot be deleted because some of it has already been used "
                         "or counted out. Correct its quantities instead.")
    delete("raw_material_batches", batch_id)


def record_purchase(purchase_date, supplier, raw_material_id, qty, unit_cost, ref, notes,
                     paid_amount=None, paid_from_sales=0.0, paid_from_profit=0.0):
    """Records a purchase AND creates its own batch, which gets used oldest-first later.
    paid_amount/paid_from_sales/paid_from_profit are just personal tracking labels -
    they never affect Profit & Loss. If paid_amount is not given, the purchase is
    assumed paid in full from sales money (keeps older behaviour unchanged)."""
    raw_material_id = int(raw_material_id)
    qty = float(qty)
    unit_cost = float(unit_cost)
    total = qty * unit_cost
    if paid_amount is None:
        paid_amount = total
        paid_from_sales = total
        paid_from_profit = 0.0
    batch = insert("raw_material_batches", {
        "raw_material_id": raw_material_id, "batch_date": purchase_date, "source": "Purchase",
        "ref": ref, "qty_in": qty, "unit_cost": unit_cost, "qty_remaining": qty})
    bid = batch[0]["id"]
    return insert("purchases", {
        "purchase_date": purchase_date, "supplier": supplier, "raw_material_id": raw_material_id,
        "qty": qty, "unit_cost": unit_cost, "ref": ref, "notes": notes, "batch_id": bid,
        "paid_amount": float(paid_amount), "paid_from_sales": float(paid_from_sales),
        "paid_from_profit": float(paid_from_profit)})


def _raw_batch_recorded_usage(batch_id):
    """Quantity from one raw batch that production/damage records say was used."""
    batch_id = int(batch_id)
    total = 0.0
    usage = get("production_batch_usage", order="id")
    if not usage.empty and "batch_id" in usage.columns:
        total += _num(usage.loc[usage["batch_id"] == batch_id, "qty_used"].sum())
    damage_usage_ids = set()
    try:
        du = get("damage_batch_usage", order="id")
    except Exception:
        du = pd.DataFrame()
    if not du.empty and "batch_id" in du.columns:
        mine = du[du["batch_id"] == batch_id]
        total += _num(mine["qty_used"].sum())
        damage_usage_ids = set(du["damage_id"].dropna().astype(int).tolist())
    damages = get("damages", order="id")
    if not damages.empty and "batch_id" in damages.columns:
        legacy = damages[(damages["batch_id"] == batch_id) & (~damages["id"].isin(damage_usage_ids))]
        if not legacy.empty:
            # Older damage rows only remembered their first batch. This is only a
            # safety guard for those rows; new damages use damage_batch_usage.
            total += _num(legacy["qty"].sum())
    return total


def update_purchase(purchase_id, purchase_date, supplier, raw_material_id, qty, unit_cost,
                    ref, notes, paid_amount, paid_from_sales, paid_from_profit):
    """Correct a purchase and its linked stock batch together.

    The amount already taken from the batch stays taken. This means the new
    quantity can be lowered only down to the amount production/damages have
    already used; the unused remainder is adjusted by the same difference.
    Costs already locked into past production/sales are not rewritten, but the
    remaining batch and all future use get the corrected purchase cost.
    """
    purchase_id = int(purchase_id)
    raw_material_id = int(raw_material_id)
    qty = float(qty)
    unit_cost = float(unit_cost)
    paid_amount = float(paid_amount)
    paid_from_sales = float(paid_from_sales)
    paid_from_profit = float(paid_from_profit)
    if qty <= 0:
        raise ValueError("Purchase quantity must be more than zero. Use Delete if the whole purchase was a mistake.")
    if unit_cost < 0 or paid_amount < 0 or paid_from_sales < 0 or paid_from_profit < 0:
        raise ValueError("Costs and paid amounts cannot be negative.")
    total = qty * unit_cost
    if paid_amount > total + 0.01:
        raise ValueError("Paid amount cannot be more than the purchase total (PKR %.2f)." % total)
    if abs((paid_from_sales + paid_from_profit) - paid_amount) > 0.01:
        raise ValueError("“Paid From Sales” plus “Paid From Profit / Pocket” must equal the Paid Amount.")

    old = _one("purchases", purchase_id)
    if not old:
        raise ValueError("That purchase could not be found.")
    payload = {
        "purchase_date": purchase_date, "supplier": (supplier or "").strip() or None,
        "raw_material_id": raw_material_id, "qty": qty, "unit_cost": unit_cost,
        "ref": (ref or "").strip() or None, "notes": (notes or "").strip() or None,
        "paid_amount": paid_amount, "paid_from_sales": paid_from_sales,
        "paid_from_profit": paid_from_profit,
    }
    batch_id = old.get("batch_id")
    stock_changed = (
        str(old.get("purchase_date")) != str(purchase_date)
        or int(_num(old.get("raw_material_id"))) != raw_material_id
        or not _close(old.get("qty"), qty)
        or not _close(old.get("unit_cost"), unit_cost)
        or (old.get("ref") or None) != payload["ref"]
    )
    if batch_id is None or pd.isna(batch_id):
        if stock_changed:
            raise ValueError("This older purchase has no linked stock batch, so its date, material, "
                             "quantity, cost or reference cannot be corrected safely from here.")
        update("purchases", purchase_id, payload)
        return

    batch = _one("raw_material_batches", int(batch_id))
    if not batch:
        raise ValueError("The stock batch linked to this purchase could not be found.")
    consumed = _num(batch.get("qty_in")) - _num(batch.get("qty_remaining"))
    recorded = _raw_batch_recorded_usage(int(batch_id))
    if qty + 1e-9 < recorded:
        raise ValueError("Quantity cannot be below %.10g, because production/damages have already used "
                         "that much from this batch. Correct those entries first." % recorded)
    new_remaining = qty - consumed
    if new_remaining < -1e-9:
        raise ValueError("Quantity cannot be that low: %.10g from this batch is already used or missing "
                         "from stock. Correct the entries that used it first." % max(consumed, 0.0))
    if int(_num(batch.get("raw_material_id"))) != raw_material_id and (consumed > 1e-9 or recorded > 1e-9):
        raise ValueError("The raw material cannot be changed after this batch has been used. "
                         "Correct or delete the production/damage that used it first.")

    old_batch_payload = {k: batch.get(k) for k in
                         ("raw_material_id", "batch_date", "ref", "qty_in", "unit_cost", "qty_remaining")}
    update("raw_material_batches", int(batch_id), {
        "raw_material_id": raw_material_id, "batch_date": purchase_date, "ref": payload["ref"],
        "qty_in": qty, "unit_cost": unit_cost, "qty_remaining": max(new_remaining, 0.0)})
    try:
        update("purchases", purchase_id, payload)
    except Exception:
        update("raw_material_batches", int(batch_id), old_batch_payload)
        raise


def delete_purchase(purchase_id):
    """Delete a purchase only while its whole batch is still unused."""
    purchase_id = int(purchase_id)
    old = _one("purchases", purchase_id)
    if not old:
        raise ValueError("That purchase could not be found.")
    batch_id = old.get("batch_id")
    if batch_id is not None and not pd.isna(batch_id):
        batch = _one("raw_material_batches", int(batch_id))
        if batch:
            recorded = _raw_batch_recorded_usage(int(batch_id))
            consumed = _num(batch.get("qty_in")) - _num(batch.get("qty_remaining"))
            if recorded > 1e-9 or consumed > 1e-9:
                raise ValueError("This purchase cannot be deleted because some of its batch has already "
                                 "been used or counted out. Correct the quantity instead, or first fix "
                                 "the production/damage entries that used it.")
        delete("purchases", purchase_id)
        if batch:
            delete("raw_material_batches", int(batch_id))
    else:
        delete("purchases", purchase_id)


def get_payables():
    """How much is owed to each supplier: total purchased, minus whatever was paid
    at the time of purchase, minus whatever's been paid since via Supplier Payments."""
    pur = get("purchases", order="id")
    if pur.empty:
        return pd.DataFrame(columns=["supplier", "purchased", "paid_at_purchase", "paid_later", "payable"])
    p = pur.copy()
    p["supplier"] = p["supplier"].fillna("Unknown Supplier").astype(str).str.strip()
    p.loc[p["supplier"] == "", "supplier"] = "Unknown Supplier"
    p["key"] = p["supplier"].str.lower()
    p["total"] = p["qty"] * p["unit_cost"]
    p["paid"] = p["paid_amount"].fillna(p["total"]) if "paid_amount" in p.columns else p["total"]
    g = p.groupby("key").agg(supplier=("supplier", "first"), purchased=("total", "sum"),
                             paid_at_purchase=("paid", "sum")).reset_index()
    pay = get("supplier_payments", order="id")
    if pay is not None and not pay.empty:
        q = pay.copy()
        q["supplier"] = q["supplier"].fillna("Unknown Supplier").astype(str).str.strip()
        q.loc[q["supplier"] == "", "supplier"] = "Unknown Supplier"
        q["key"] = q["supplier"].str.lower()
        gp = q.groupby("key").agg(paid_later=("amount", "sum")).reset_index()
        g = g.merge(gp[["key", "paid_later"]], on="key", how="left")
    else:
        g["paid_later"] = 0.0
    g["paid_later"] = g["paid_later"].fillna(0.0)
    g["payable"] = g["purchased"] - g["paid_at_purchase"] - g["paid_later"]
    return g[["supplier", "purchased", "paid_at_purchase", "paid_later", "payable"]]


def record_supplier_payment(payment_date, supplier, amount, paid_from_sales, paid_from_profit, method, notes):
    """Pays down what's owed to a supplier for earlier credit purchases. This is a
    personal tracking label only - it never affects Profit & Loss."""
    return insert("supplier_payments", {
        "payment_date": payment_date, "supplier": supplier, "amount": float(amount),
        "paid_from_sales": float(paid_from_sales), "paid_from_profit": float(paid_from_profit),
        "method": method, "notes": notes})


def record_production(production_date, batch_ref, product_id, bundles, notes, recipe_df):
    """Uses raw material batches oldest-first, locks in the real cost of this production
    run, and remembers exactly which batches were used so the cost never changes later."""
    product_id = int(product_id)
    bundles = float(bundles)
    need = recipe_df[recipe_df["product_id"] == product_id]
    shortages = []
    for _, rc in need.iterrows():
        qty_needed = float(rc["qty_per_bundle"]) * bundles
        if qty_needed <= 0:
            continue
        _plan, short = fifo_plan(int(rc["raw_material_id"]), qty_needed)
        if short > 1e-9:
            shortages.append("material ID " + str(int(rc["raw_material_id"]))
                             + " short by " + format(short, "g"))
    if shortages:
        raise ValueError("Not enough raw-material batch stock for this production ("
                         + "; ".join(shortages) + "). Nothing was saved.")
    usage, total_cost = [], 0.0
    for _, rc in need.iterrows():
        qty_needed = float(rc["qty_per_bundle"]) * bundles
        if qty_needed <= 0:
            continue
        plan = consume_fifo(int(rc["raw_material_id"]), qty_needed)
        for p in plan:
            total_cost += p["qty"] * p["unit_cost"]
            usage.append({"raw_material_id": int(rc["raw_material_id"]), "batch_id": p["batch_id"],
                         "qty_used": p["qty"], "unit_cost": p["unit_cost"]})
    prod = insert("production", {
        "production_date": production_date, "batch_ref": batch_ref, "product_id": product_id,
        "bundles": bundles, "notes": notes, "total_cost": total_cost, "qty_remaining": bundles})
    pid = prod[0]["id"]
    if usage:
        insert("production_batch_usage", [{**u, "production_id": pid} for u in usage])
    return pid, total_cost


def _production_usage_rows(production_id):
    usage = get("production_batch_usage", order="id")
    if usage.empty:
        return []
    return usage[usage["production_id"] == int(production_id)].to_dict("records")


def _production_recorded_outflow(production_id):
    """Bundles from one production run that sale/damage records say left stock."""
    production_id = int(production_id)
    total = 0.0
    sales = get("sale_batch_usage", order="id")
    if not sales.empty and "production_id" in sales.columns:
        total += _num(sales.loc[sales["production_id"] == production_id, "qty_used"].sum())
    damage_usage_ids = set()
    try:
        du = get("damage_batch_usage", order="id")
    except Exception:
        du = pd.DataFrame()
    if not du.empty and "production_id" in du.columns:
        mine = du[du["production_id"] == production_id]
        total += _num(mine["qty_used"].sum())
        damage_usage_ids = set(du["damage_id"].dropna().astype(int).tolist())
    damages = get("damages", order="id")
    if not damages.empty and "fg_batch_id" in damages.columns:
        legacy = damages[(damages["fg_batch_id"] == production_id)
                         & (~damages["id"].isin(damage_usage_ids))]
        if not legacy.empty:
            total += _num(legacy["qty"].sum())
    return total


def update_production(production_id, production_date, batch_ref, product_id, bundles, notes):
    """Correct a production run.

    Date/reference/notes can always be corrected. Product or bundle quantity
    can be corrected while the whole run is still in stock: its raw materials
    are put back into their exact batches, then taken again for the corrected
    run. If bundles from the run were already sold, damaged or counted out,
    those dependent entries must be corrected first so locked sale costs stay
    truthful.
    """
    production_id = int(production_id)
    product_id = int(product_id)
    bundles = float(bundles)
    if bundles <= 0:
        raise ValueError("Bundles produced must be more than zero. Use Delete if the whole run was a mistake.")
    old = _one("production", production_id)
    if not old:
        raise ValueError("That production entry could not be found.")
    base_payload = {
        "production_date": production_date,
        "batch_ref": (batch_ref or "").strip() or None,
        "product_id": product_id,
        "bundles": bundles,
        "notes": (notes or "").strip() or None,
    }
    if int(_num(old.get("product_id"))) == product_id and _close(old.get("bundles"), bundles):
        update("production", production_id, base_payload)
        return

    outflow = _production_recorded_outflow(production_id)
    unexplained = _num(old.get("bundles")) - _num(old.get("qty_remaining")) - outflow
    if outflow > 1e-9 or unexplained > 1e-9:
        bits = []
        if outflow > 1e-9:
            bits.append("%.10g bundle(s) were already sold or damaged" % outflow)
        if unexplained > 1e-9:
            bits.append("%.10g bundle(s) were already counted out" % unexplained)
        raise ValueError("Product/bundles cannot be changed for this run because " + " and ".join(bits)
                         + ". Date, batch reference and notes can still be edited. To change the "
                         "product or bundles, first correct the invoice/damage/physical-count entries "
                         "that took stock from this run.")

    usage = _production_usage_rows(production_id)
    if not usage:
        # Opening / physical-count finished batches have a manually entered cost
        # and no raw-material usage. Preserve that cost per bundle.
        old_bundles = _num(old.get("bundles")) or 1.0
        unit_cost = _num(old.get("total_cost")) / old_bundles
        payload = {**base_payload, "total_cost": unit_cost * bundles, "qty_remaining": bundles}
        update("production", production_id, payload)
        return

    required = {}
    if int(_num(old.get("product_id"))) == product_id:
        # Same product: scale the actual raw materials this run used, rather
        # than assuming today's recipe is the recipe that was used back then.
        scale = bundles / (_num(old.get("bundles")) or 1.0)
        for u in usage:
            mid = int(u["raw_material_id"])
            required[mid] = required.get(mid, 0.0) + _num(u.get("qty_used")) * scale
    else:
        recipe = get("recipe", order="id")
        rows = recipe[recipe["product_id"] == product_id] if not recipe.empty else recipe
        if rows is None or rows.empty:
            raise ValueError("The corrected product has no recipe yet. Add its recipe first.")
        for _, rc in rows.iterrows():
            qty_needed = _num(rc.get("qty_per_bundle")) * bundles
            if qty_needed > 0:
                required[int(rc["raw_material_id"])] = qty_needed

    old_by_material = {}
    for u in usage:
        mid = int(u["raw_material_id"])
        old_by_material[mid] = old_by_material.get(mid, 0.0) + _num(u.get("qty_used"))
    for mid, qty_needed in required.items():
        batches = get_batches(mid, only_available=False)
        available = _num(batches["qty_remaining"].sum()) if not batches.empty else 0.0
        available += old_by_material.get(mid, 0.0)
        if qty_needed > available + 1e-9:
            raise ValueError("Not enough recorded raw-material stock for the corrected production "
                             "(material ID %s is short by %.10g after putting this run's old "
                             "materials back). Nothing was changed." % (mid, qty_needed - available))

    old_snapshot = {k: old.get(k) for k in
                    ("production_date", "batch_ref", "product_id", "bundles", "notes",
                     "total_cost", "qty_remaining")}
    new_usage = []
    inserted_ids = []
    old_restored = False
    old_usage_deleted = False
    try:
        _restore_raw_usage(usage)
        old_restored = True
        delete_ids("production_batch_usage", [u["id"] for u in usage])
        old_usage_deleted = True
        total_cost = 0.0
        for mid, qty_needed in required.items():
            plan = consume_fifo(mid, qty_needed)
            for p in plan:
                total_cost += p["qty"] * p["unit_cost"]
                new_usage.append({"production_id": production_id, "raw_material_id": mid,
                                  "batch_id": p["batch_id"], "qty_used": p["qty"],
                                  "unit_cost": p["unit_cost"]})
        if new_usage:
            inserted = insert("production_batch_usage", new_usage)
            inserted_ids = [r["id"] for r in inserted]
        update("production", production_id,
               {**base_payload, "total_cost": total_cost, "qty_remaining": bundles})
    except Exception:
        # Best-effort rollback in this single-user app if a later write fails.
        if inserted_ids:
            delete_ids("production_batch_usage", inserted_ids)
        if new_usage:
            _restore_raw_usage([{**u, "qty_used": u["qty_used"]} for u in new_usage])
        if old_restored:
            _take_exact_raw_usage(usage)
        if old_usage_deleted:
            insert("production_batch_usage", [
                {"production_id": production_id, "raw_material_id": int(u["raw_material_id"]),
                 "batch_id": int(u["batch_id"]), "qty_used": _num(u.get("qty_used")),
                 "unit_cost": _num(u.get("unit_cost"))} for u in usage])
        update("production", production_id, old_snapshot)
        raise


def delete_production(production_id):
    """Delete an unused production run and return its raw materials to stock."""
    production_id = int(production_id)
    old = _one("production", production_id)
    if not old:
        raise ValueError("That production entry could not be found.")
    outflow = _production_recorded_outflow(production_id)
    unexplained = _num(old.get("bundles")) - _num(old.get("qty_remaining")) - outflow
    if outflow > 1e-9 or unexplained > 1e-9:
        raise ValueError("This production run cannot be deleted because some of its bundles were "
                         "already sold, damaged or counted out. Correct those entries first.")
    usage = _production_usage_rows(production_id)
    _restore_raw_usage(usage)
    try:
        delete("production", production_id)
    except Exception:
        _take_exact_raw_usage(usage)
        raise


def _damage_usage_rows(damage_id):
    try:
        usage = get("damage_batch_usage", order="id")
    except Exception:
        return []
    if usage.empty:
        return []
    return usage[usage["damage_id"] == int(damage_id)].to_dict("records")


def _damage_usage_copy(old, usage):
    """Clean copies of damage batch rows, safe to re-insert during rollback."""
    rows = []
    for u in usage:
        row = {"damage_id": int(_num(u.get("damage_id"))),
               "qty_used": _num(u.get("qty_used")), "unit_cost": _num(u.get("unit_cost"))}
        if old.get("damage_type") == "Raw Material":
            row.update({"raw_material_id": int(_num(u.get("raw_material_id"))),
                        "batch_id": int(_num(u.get("batch_id")))})
        else:
            row.update({"product_id": int(_num(u.get("product_id"))),
                        "production_id": int(_num(u.get("production_id")))})
        rows.append(row)
    return rows


def _check_damage_usage_complete(old, usage):
    total = sum(_num(u.get("qty_used")) for u in usage)
    if not _close(total, old.get("qty")):
        raise ValueError("This damage entry's batch record adds up to %.10g, but the damage "
                         "quantity is %.10g. Nothing was changed; that batch record needs "
                         "checking before the item/quantity can be edited safely."
                         % (total, _num(old.get("qty"))))
    return total


def _insert_damage_usage(damage_id, damage_type, raw_material_id, product_id, plan):
    rows = []
    for p in plan:
        row = {"damage_id": int(damage_id), "qty_used": float(p["qty"]),
               "unit_cost": float(p["unit_cost"])}
        if damage_type == "Raw Material":
            row.update({"raw_material_id": int(raw_material_id), "batch_id": int(p["batch_id"])})
        else:
            row.update({"product_id": int(product_id), "production_id": int(p["production_id"])})
        rows.append(row)
    return insert("damage_batch_usage", rows) if rows else []


def record_raw_damage(damage_date, raw_material_id, qty, reason, notes):
    """Raw material damage: takes the loss from the oldest batch(es), at their real cost."""
    raw_material_id = int(raw_material_id)
    qty = float(qty)
    plan = consume_fifo(raw_material_id, qty)
    total = sum(p["qty"] * p["unit_cost"] for p in plan)
    avg_cost = total / qty if qty else 0.0
    try:
        rows = insert("damages", {
            "damage_date": damage_date, "damage_type": "Raw Material", "raw_material_id": raw_material_id,
            "product_id": None, "qty": qty, "reason": reason, "notes": notes,
            "unit_cost_at_time": avg_cost, "batch_id": plan[0]["batch_id"] if plan else None})
        try:
            _insert_damage_usage(rows[0]["id"], "Raw Material", raw_material_id, None, plan)
        except Exception:
            delete("damages", rows[0]["id"])
            raise
        return rows
    except Exception:
        _restore_raw_usage([{"batch_id": p["batch_id"], "qty_used": p["qty"]} for p in plan])
        raise


# ======================================================= FINISHED GOODS BATCHES
def get_fg_batches(product_id, only_available=True):
    """Every production run for one product, oldest first - these are the finished-goods batches."""
    df = get("production", order="production_date")
    if df.empty:
        return df
    df = df[df["product_id"] == int(product_id)]
    if only_available:
        df = df[df["qty_remaining"] > 0]
    return df.sort_values(["production_date", "id"]).reset_index(drop=True)


def fg_fifo_plan(product_id, qty_needed):
    """PREVIEW ONLY - changes nothing. Returns (plan, shortfall)."""
    qty_needed = float(qty_needed)
    plan, remaining = [], qty_needed
    for _, b in get_fg_batches(product_id).iterrows():
        if remaining <= 1e-9:
            break
        take = min(float(b["qty_remaining"]), remaining)
        if take <= 0:
            continue
        bundles = float(b["bundles"]) or 1.0
        unit_cost = float(b["total_cost"] or 0) / bundles
        plan.append({"production_id": int(b["id"]), "production_date": b["production_date"],
                     "qty": take, "unit_cost": unit_cost})
        remaining -= take
    return plan, max(remaining, 0.0)


def consume_fg_fifo(product_id, qty_needed):
    """Takes finished stock out of the oldest production run(s) first. If there isn't enough
    recorded finished stock, NOTHING is changed and a clear error is raised - finished
    stock is never invented. Record the missing production first, then retry."""
    product_id = int(product_id)
    qty_needed = float(qty_needed)
    all_batches = get_fg_batches(product_id, only_available=False)
    avail = all_batches[all_batches["qty_remaining"] > 0] if not all_batches.empty else all_batches
    plan, updates, remaining = [], [], qty_needed
    for _, b in avail.iterrows():
        if remaining <= 1e-9:
            break
        take = min(float(b["qty_remaining"]), remaining)
        if take <= 0:
            continue
        bundles = float(b["bundles"]) or 1.0
        unit_cost = float(b["total_cost"] or 0) / bundles
        plan.append({"production_id": int(b["id"]), "production_date": b["production_date"],
                     "qty": take, "unit_cost": unit_cost})
        updates.append((int(b["id"]), float(b["qty_remaining"]) - take))
        remaining -= take
    if remaining > 1e-9:
        raise ValueError("Not enough recorded finished stock (product ID "
                         + str(product_id) + "): short by " + format(remaining, "g")
                         + " bundle(s). Nothing was changed by this step. Record the "
                         "missing production first, then try again.")
    for pid_, new_rem in updates:
        _client().table("production").update({"qty_remaining": new_rem}).eq("id", pid_).execute()
    st.cache_data.clear()
    return plan


def restore_fg_batches(usage_rows):
    """Reverses previously-consumed finished-goods batch usage (adds the quantity back)."""
    for _, u in usage_rows.iterrows():
        row = _client().table("production").select("qty_remaining").eq("id", int(u["production_id"])).limit(1).execute().data
        if row:
            new_rem = float(row[0]["qty_remaining"]) + float(u["qty_used"])
            _client().table("production").update({"qty_remaining": new_rem}).eq("id", int(u["production_id"])).execute()
    st.cache_data.clear()


def consume_invoice_line_fg(invoice_line_id, product_id, qty):
    """Consumes finished-goods batches FIFO for one invoice line, remembers which batches
    were used, and locks in the real cost of goods sold for that line. Returns the cost."""
    plan = consume_fg_fifo(product_id, qty)
    total = sum(p["qty"] * p["unit_cost"] for p in plan)
    if plan:
        insert("sale_batch_usage", [{"invoice_line_id": int(invoice_line_id), "product_id": int(product_id),
                                     "production_id": p["production_id"], "qty_used": p["qty"],
                                     "unit_cost": p["unit_cost"]} for p in plan])
    update("invoice_lines", invoice_line_id, {"cogs_amount": total})
    return total


def reverse_invoice_lines(invoice_id):
    """Restores finished-goods batch quantities for every line of an invoice and clears the
    batch-usage record. Always call this BEFORE deleting or replacing an invoice's lines."""
    il = get("invoice_lines", order="id")
    il = il[il["invoice_id"] == int(invoice_id)]
    if il.empty:
        return
    usage = get("sale_batch_usage", order="id")
    if usage.empty:
        return
    line_ids = il["id"].tolist()
    u = usage[usage["invoice_line_id"].isin(line_ids)]
    if not u.empty:
        restore_fg_batches(u)
        delete_ids("sale_batch_usage", u["id"].tolist())


def record_fg_damage(damage_date, product_id, qty, reason, notes):
    """Finished-goods damage: takes the loss from the oldest production batch(es), at their real cost."""
    product_id = int(product_id)
    qty = float(qty)
    plan = consume_fg_fifo(product_id, qty)
    total = sum(p["qty"] * p["unit_cost"] for p in plan)
    avg_cost = total / qty if qty else 0.0
    try:
        rows = insert("damages", {
            "damage_date": damage_date, "damage_type": "Finished Goods", "raw_material_id": None,
            "product_id": product_id, "qty": qty, "reason": reason, "notes": notes,
            "unit_cost_at_time": avg_cost, "fg_batch_id": plan[0]["production_id"] if plan else None})
        try:
            _insert_damage_usage(rows[0]["id"], "Finished Goods", None, product_id, plan)
        except Exception:
            delete("damages", rows[0]["id"])
            raise
        return rows
    except Exception:
        _restore_fg_usage([{"production_id": p["production_id"], "qty_used": p["qty"]} for p in plan])
        raise


def update_damage(damage_id, damage_date, damage_type, raw_material_id, product_id, qty, reason, notes):
    """Correct a saved damage line.

    Date/reason/notes are simple corrections. If type, item or quantity changes,
    the old quantity is first put back into the exact batch(es) it came from;
    the corrected damage is then taken oldest-first again and its loss cost is
    recalculated from those real batches.
    """
    damage_id = int(damage_id)
    qty = float(qty)
    if qty <= 0:
        raise ValueError("Damage quantity must be more than zero. Use Delete if the whole damage was a mistake.")
    if damage_type == "Raw Material":
        if raw_material_id is None:
            raise ValueError("Choose the raw material.")
        raw_material_id = int(raw_material_id)
        product_id = None
    elif damage_type == "Finished Goods":
        if product_id is None:
            raise ValueError("Choose the product.")
        product_id = int(product_id)
        raw_material_id = None
    else:
        raise ValueError("Choose whether this was Raw Material or Finished Goods.")

    old = _one("damages", damage_id)
    if not old:
        raise ValueError("That damage entry could not be found.")
    payload = {
        "damage_date": damage_date, "damage_type": damage_type,
        "raw_material_id": raw_material_id, "product_id": product_id,
        "qty": qty, "reason": reason, "notes": (notes or "").strip() or None,
    }
    stock_changed = (
        old.get("damage_type") != damage_type
        or int(_num(old.get("raw_material_id"))) != int(_num(raw_material_id))
        or int(_num(old.get("product_id"))) != int(_num(product_id))
        or not _close(old.get("qty"), qty)
    )
    if not stock_changed:
        update("damages", damage_id, payload)
        return

    usage = _damage_usage_rows(damage_id)
    if not usage:
        raise ValueError("This older damage entry does not remember every batch it used, so its "
                         "date/reason/notes can be edited, but its type/item/quantity cannot be "
                         "changed safely. New damage entries remember their exact batches.")

    old_qty = _check_damage_usage_complete(old, usage)
    if damage_type == "Raw Material":
        batches = get_batches(raw_material_id, only_available=False)
        available = _num(batches["qty_remaining"].sum()) if not batches.empty else 0.0
        if old.get("damage_type") == "Raw Material" and int(_num(old.get("raw_material_id"))) == raw_material_id:
            available += old_qty
    else:
        batches = get_fg_batches(product_id, only_available=False)
        available = _num(batches["qty_remaining"].sum()) if not batches.empty else 0.0
        if old.get("damage_type") == "Finished Goods" and int(_num(old.get("product_id"))) == product_id:
            available += old_qty
    if qty > available + 1e-9:
        raise ValueError("Not enough recorded stock for the corrected damage (short by %.10g after "
                         "putting the old damage back). Nothing was changed." % (qty - available))

    old_snapshot = {k: old.get(k) for k in
                    ("damage_date", "damage_type", "raw_material_id", "product_id", "qty",
                     "reason", "notes", "unit_cost_at_time", "batch_id", "fg_batch_id")}
    new_usage = []
    inserted_ids = []
    old_restored = False
    old_usage_deleted = False
    try:
        if old.get("damage_type") == "Raw Material":
            _restore_raw_usage(usage)
        else:
            _restore_fg_usage(usage)
        old_restored = True
        delete_ids("damage_batch_usage", [u["id"] for u in usage])
        old_usage_deleted = True

        if damage_type == "Raw Material":
            plan = consume_fifo(raw_material_id, qty)
            new_usage = [{"damage_id": damage_id, "raw_material_id": raw_material_id,
                          "batch_id": p["batch_id"], "qty_used": p["qty"],
                          "unit_cost": p["unit_cost"]} for p in plan]
            first_batch = plan[0]["batch_id"] if plan else None
            first_fg_batch = None
        else:
            plan = consume_fg_fifo(product_id, qty)
            new_usage = [{"damage_id": damage_id, "product_id": product_id,
                          "production_id": p["production_id"], "qty_used": p["qty"],
                          "unit_cost": p["unit_cost"]} for p in plan]
            first_batch = None
            first_fg_batch = plan[0]["production_id"] if plan else None
        total = sum(p["qty"] * p["unit_cost"] for p in plan)
        if new_usage:
            inserted = insert("damage_batch_usage", new_usage)
            inserted_ids = [r["id"] for r in inserted]
        update("damages", damage_id, {**payload,
                                      "unit_cost_at_time": total / qty if qty else 0.0,
                                      "batch_id": first_batch, "fg_batch_id": first_fg_batch})
    except Exception:
        if inserted_ids:
            delete_ids("damage_batch_usage", inserted_ids)
        if new_usage:
            if damage_type == "Raw Material":
                _restore_raw_usage(new_usage)
            else:
                _restore_fg_usage(new_usage)
        if old_restored:
            if old.get("damage_type") == "Raw Material":
                _take_exact_raw_usage(usage)
            else:
                _take_exact_fg_usage(usage)
        if old_usage_deleted:
            insert("damage_batch_usage", _damage_usage_copy(old, usage))
        update("damages", damage_id, old_snapshot)
        raise


def delete_damage(damage_id):
    """Delete a damage and put its quantity back into the exact batch(es)."""
    damage_id = int(damage_id)
    old = _one("damages", damage_id)
    if not old:
        raise ValueError("That damage entry could not be found.")
    usage = _damage_usage_rows(damage_id)
    if not usage:
        raise ValueError("This older damage entry does not remember every batch it used, so it "
                         "cannot be deleted safely from here.")
    _check_damage_usage_complete(old, usage)
    if old.get("damage_type") == "Raw Material":
        _restore_raw_usage(usage)
    else:
        _restore_fg_usage(usage)
    try:
        delete("damages", damage_id)
    except Exception:
        if old.get("damage_type") == "Raw Material":
            _take_exact_raw_usage(usage)
        else:
            _take_exact_fg_usage(usage)
        raise


# ====================================================== STOCK SET-UP & COUNTS
def create_raw_material(code, name, unit, opening_qty, opening_unit_cost):
    """Creates a raw material AND its opening batch, so the batch register and the
    stock register agree from day one."""
    opening_qty = float(opening_qty)
    opening_unit_cost = float(opening_unit_cost)
    mat = insert("raw_materials", {"code": code, "name": name, "unit": unit or "Pcs",
                                   "opening_stock": opening_qty,
                                   "opening_unit_cost": opening_unit_cost})[0]
    if opening_qty > 0:
        try:
            insert("raw_material_batches", {
                "raw_material_id": int(mat["id"]), "batch_date": dt.date.today().isoformat(),
                "source": "Opening (Day Zero)", "ref": "Opening stock",
                "qty_in": opening_qty, "unit_cost": opening_unit_cost,
                "qty_remaining": opening_qty})
        except Exception:
            delete("raw_materials", int(mat["id"]))
            raise
    return mat


def create_product(code, name, min_stock, opening_qty, opening_unit_cost):
    """Creates a product AND (if opening bundles are given) an opening finished-goods
    batch for them, so sales can draw on real recorded stock at a real cost."""
    opening_qty = float(opening_qty)
    opening_unit_cost = float(opening_unit_cost)
    prod = insert("products", {"code": code, "name": name, "opening_stock": 0,
                               "min_stock": float(min_stock) if min_stock and float(min_stock) > 0 else None})[0]
    if opening_qty > 0:
        try:
            insert("production", {
                "production_date": dt.date.today().isoformat(), "batch_ref": "Opening Stock",
                "product_id": int(prod["id"]), "bundles": opening_qty,
                "notes": "Opening finished stock entered when the product was created",
                "total_cost": opening_qty * opening_unit_cost, "qty_remaining": opening_qty})
        except Exception:
            delete("products", int(prod["id"]))
            raise
    return prod


def adjust_raw_physical_count(raw_material_id, counted, reorder_level):
    """Makes recorded raw-material batch stock match a physical count. Extra stock
    becomes a visible 'Physical Count Adjustment' batch; missing stock is taken off
    the newest batch(es) first. Both stock registers read the batches, so they stay
    in agreement."""
    raw_material_id = int(raw_material_id)
    counted = float(counted)
    batches = get_batches(raw_material_id, only_available=False)
    current = float(batches["qty_remaining"].sum()) if not batches.empty else 0.0
    delta = counted - current
    if delta > 1e-9:
        if not batches.empty and current > 0:
            cost = float((batches["qty_remaining"] * batches["unit_cost"]).sum()) / current
        elif not batches.empty:
            cost = float(batches.sort_values(["batch_date", "id"]).iloc[-1]["unit_cost"])
        else:
            rm = get("raw_materials", order="id")
            row = rm[rm["id"] == raw_material_id] if not rm.empty else rm
            cost = float(row.iloc[0]["opening_unit_cost"]) if not row.empty else 0.0
        insert("raw_material_batches", {
            "raw_material_id": raw_material_id, "batch_date": dt.date.today().isoformat(),
            "source": "Physical Count Adjustment", "ref": "Stock counted higher than recorded",
            "qty_in": delta, "unit_cost": cost, "qty_remaining": delta})
    elif delta < -1e-9:
        need = -delta
        avail = get_batches(raw_material_id).sort_values(["batch_date", "id"], ascending=False)
        for _, b in avail.iterrows():
            if need <= 1e-9:
                break
            take = min(float(b["qty_remaining"]), need)
            if take <= 0:
                continue
            update("raw_material_batches", int(b["id"]), {
                "qty_in": float(b["qty_in"]) - take,
                "qty_remaining": float(b["qty_remaining"]) - take})
            need -= take
    update("raw_materials", raw_material_id, {"reorder_level": float(reorder_level)})
    return delta


def adjust_fg_physical_count(product_id, counted, min_stock, fallback_unit_cost=0.0):
    """Makes recorded finished-goods batches match a physical count. Extra bundles
    become a visible 'Physical Count Adjustment' production batch; missing bundles
    are taken off the newest batch(es) first."""
    product_id = int(product_id)
    counted = float(counted)
    batches = get_fg_batches(product_id, only_available=False)
    current = float(batches["qty_remaining"].sum()) if not batches.empty else 0.0
    delta = counted - current
    if delta > 1e-9:
        cost = float(fallback_unit_cost or 0.0)
        if cost <= 0 and not batches.empty:
            last = batches.sort_values(["production_date", "id"]).iloc[-1]
            cost = float(last["total_cost"] or 0) / (float(last["bundles"]) or 1.0)
        insert("production", {
            "production_date": dt.date.today().isoformat(),
            "batch_ref": "Physical Count Adjustment", "product_id": product_id,
            "bundles": delta, "notes": "Stock counted higher than recorded",
            "total_cost": delta * cost, "qty_remaining": delta})
    elif delta < -1e-9:
        need = -delta
        avail = get_fg_batches(product_id).sort_values(["production_date", "id"], ascending=False)
        for _, b in avail.iterrows():
            if need <= 1e-9:
                break
            take = min(float(b["qty_remaining"]), need)
            if take <= 0:
                continue
            update("production", int(b["id"]),
                   {"qty_remaining": float(b["qty_remaining"]) - take})
            need -= take
    update("products", product_id, {"min_stock": float(min_stock)})
    return delta
