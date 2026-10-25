import io
import re

import pandas as pd
import streamlit as st

PAGE = 1000
METHODS = ["Cash", "Bank Transfer", "Easypaisa / JazzCash", "Cheque", "Other"]
EXPORT_SHEETS = ["customers", "products", "raw_materials", "recipe", "invoices", "invoice_lines",
                 "payments", "purchases", "production", "damages", "expenses",
                 "v_invoice_summary", "v_raw_stock", "v_product_stock"]
OPTIONAL_SHEETS = ["suppliers", "sale_orders", "sale_order_lines"]


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
