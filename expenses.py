import datetime as dt

import pandas as pd
import streamlit as st

import db
import ui

ui.header("Expenses & Draws", "Plant expenses and your personal withdrawals, kept apart")

exp = db.get("expenses", order="id")
DEFAULT_CATS = ["Fuel Cost", "Electricity Bill", "Gas LPG", "Subscriptions", "Labour / Salaries",
                "Transport / Delivery", "Repairs & Maintenance", "Rent", "Filters & Chemicals", "Other"]
op = exp[exp["type"] == "OPERATING"] if not exp.empty else exp
dr = exp[exp["type"] == "OWNER DRAW"] if not exp.empty else exp

k1, k2, k3 = st.columns(3)
k1.metric("Plant expenses", "PKR " + ui.money(op["amount"].sum() if not op.empty else 0))
k2.metric("Owner draws", "PKR " + ui.money(dr["amount"].sum() if not dr.empty else 0))
k3.metric("Entries", str(len(exp)))

st.markdown("#### Add an entry")
n = st.session_state.setdefault("exp_n", 0)
kind = st.radio("What is this?", ["Plant expense", "Owner draw (personal withdrawal)"], horizontal=True,
                key="exp_kind_" + str(n))
is_draw = kind.startswith("Owner")
a, b, c = st.columns(3)
d = a.date_input("Date", value=dt.date.today(), key="exp_d_" + str(n))
amount = b.number_input("Amount (PKR)", min_value=0.0, step=100.0, key="exp_a_" + str(n))
if is_draw:
    category = "Profit Deducted"
    c.text_input("Category", value=category, disabled=True, key="exp_cdis_" + str(n))
else:
    cats = list(DEFAULT_CATS)
    if not op.empty:
        cats += [x for x in op["category"].dropna().unique().tolist() if x not in cats]
    category = c.selectbox("Category", cats, key="exp_c_" + str(n))
    custom = st.text_input("Or type a new category (optional)", key="exp_new_" + str(n))
    if custom.strip():
        category = custom.strip()
notes = st.text_input("Notes (optional)", key="exp_notes_" + str(n))

if st.button("Save entry", type="primary", key="exp_save_" + str(n)):
    if amount <= 0:
        st.error("Enter an amount.")
    else:
        try:
            db.insert("expenses", {
                "entry_no": db.next_no(exp["entry_no"].tolist() if not exp.empty else [], "E#"),
                "expense_date": d.isoformat(), "category": category,
                "type": "OWNER DRAW" if is_draw else "OPERATING",
                "amount": float(amount), "notes": notes or None})
            st.session_state["exp_n"] = n + 1
            st.session_state["flash"] = ("Owner draw" if is_draw else "Expense") + " of PKR " + ui.money(amount) + " saved."
            st.rerun()
        except Exception as e:
            st.error("Could not save: " + str(e))

st.write("")
t1, t2, t3 = st.tabs(["Plant expenses", "Owner draws", "By category"])


def history(df, key):
    if df.empty:
        st.info("Nothing recorded yet.")
        return
    h = df.sort_values(["expense_date", "id"], ascending=False)
    show = ui.fmt(h[["entry_no", "expense_date", "category", "amount", "notes"]], ["amount"])
    show.columns = ["Entry", "Date", "Category", "Amount", "Notes"]
    ui.table(show)
    ui.delete_entry("expenses", h, lambda r: str(r["expense_date"]) + " · " + str(r["category"]) + " · " + ui.money(r["amount"]), key)


with t1:
    history(op, "exp_op")
with t2:
    history(dr, "exp_dr")
with t3:
    if op.empty:
        st.info("No plant expenses yet.")
    else:
        by = op.groupby("category")["amount"].sum().sort_values(ascending=False)
        st.bar_chart(by, color=ui.ACCENT)
        m = op.assign(month=pd.to_datetime(op["expense_date"]).dt.strftime("%Y-%m"))
        pivot = m.pivot_table(index="category", columns="month", values="amount", aggfunc="sum", fill_value=0)
        pivot["Total"] = pivot.sum(axis=1)
        pivot = pivot.sort_values("Total", ascending=False).reset_index()
        ui.table(ui.fmt(pivot, [c for c in pivot.columns if c != "category"]).rename(columns={"category": "Category"}))
