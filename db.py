import datetime as dt
import io
import re

import pandas as pd
import streamlit as st

PAGE = 1000
METHODS = ["Cash", "Bank Transfer", "Easypaisa / JazzCash", "Cheque", "Other"]
EXPORT_SHEETS = ["customers", "products", "raw_materials", "recipe", "invoices", "invoice_lines",
                 "payments", "purchases", "production", "damages", "expenses",
                 "v_invoice_summary", "v_raw_stock", "v_product_stock"]
OPTIONAL_SHEETS = ["suppliers", "sale_orders", "sale_order_lines", "raw_material_batches",
                   "production_batch_usage", "sale_batch_usage", "supplier_payments"]


@st.cache_resource
def _client():
    from supabase import create_client
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


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


@st.cache_data(ttl=60, show_spinner=False)
def has_split():
    """True once orca_update_2.sql has been run (purchases know where the money came from)."""
    try:
        _client().table("purchases").select("paid_from_sales").limit(1).execute()
        return True
    except Exception:
        return False


def reinvest():
    """How much sales money and profit money has gone back into raw materials."""
    pnl = get("v_pnl")
    pur = get("purchases", order="id")
    cogs = float(pnl.iloc[0]["cogs"]) if not pnl.empty else 0.0
    current = float(pnl.iloc[0]["net_retained_profit"]) if not pnl.empty else 0.0
    from_sales = from_profit = 0.0
    if not pur.empty and "paid_from_sales" in pur.columns:
        from_sales = float(pur["paid_from_sales"].fillna(0).sum())
        from_profit = float(pur["paid_from_profit"].fillna(0).sum())
    return {"enabled": has_split(), "cogs": cogs, "current_profit": current,
            "from_sales": from_sales, "from_profit": from_profit,
            "left_to_reinvest": cogs - from_sales, "profit_in_hand": current - from_profit}


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
    recorded batch stock, it automatically creates a small catch-up batch (at the last
    known price) so the numbers stay balanced, instead of blocking you from saving.
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
        fallback_cost = float(all_batches.sort_values("batch_date").iloc[-1]["unit_cost"]) if not all_batches.empty else 0.0
        made = insert("raw_material_batches", {
            "raw_material_id": raw_material_id, "batch_date": dt.date.today().isoformat(),
            "source": "Auto (Stock Shortfall)",
            "ref": "Created automatically because recorded batch stock ran out",
            "qty_in": remaining, "unit_cost": fallback_cost, "qty_remaining": 0})
        plan.append({"batch_id": made[0]["id"], "batch_date": dt.date.today().isoformat(),
                     "qty": remaining, "unit_cost": fallback_cost})
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
    usage, total_cost = [], 0.0
    for _, rc in need.iterrows():
        qty_needed = float(rc["qty_per_bundle"]) * 
