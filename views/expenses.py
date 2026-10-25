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
k1.metric("Plant Expenses", "PKR " + ui.money(op["amount"].sum() if not op.empty else 0))
k2.metric("Owner Draws", "PKR " + ui.money(dr["amount"].sum() if not dr.empty else 0))
k3.metric("Entries", str(len(exp)))

with st.expander("Add An Entry", expanded=True):
    n = st.session_state.setdefault("exp_n", 0)
    kind = st.radio("What Is This?", ["Plant Expense", "Owner Draw (Personal Withdrawal)"], horizontal=True,
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
        custom = st.text_input("Or Type A New Category (Optional)", key="exp_new_" + str(n))
        if custom.strip():
            category = custom.strip()
    notes = st.text_input("Notes (Optional)", key="exp_notes_" + str(n))
    if st.button("Save Entry", type="primary", key="exp_save_" + str(n)):
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

section = ui.sections(["Plant Expenses", "Owner Draws", "By Category"], "exp_tab")


def history(df, key, draw):
    if df.empty:
        st.info("Nothing recorded yet.")
        return
    h = df.sort_values(["expense_date", "id"], ascending=False)
    fields = [{"col": "expense_date", "label": "Date", "kind": "date"},
              {"col": "amount", "label": "Amount (PKR)", "kind": "num", "step": 100.0},
              {"col": "notes", "label": "Notes"}]
    if not draw:
        fields.insert(1, {"col": "category", "label": "Category", "required": True})
    ui.entity_table(
        key, h,
        [("Entry", "entry_no", None), ("Date", "expense_date", None), ("Category", "category", None),
         ("Amount", "amount", 0), ("Notes", "notes", None)],
        table="expenses", fields=fields,
        label=lambda r: str(r["expense_date"]) + "  ·  " + str(r["category"]) + "  ·  PKR " + ui.money(r["amount"]))


if section == "Plant Expenses":
    history(op, "exp_op", False)
elif section == "Owner Draws":
    history(dr, "exp_dr", True)
else:
    if op.empty:
        st.info("No plant expenses yet.")
    else:
        by = op.groupby("category")["amount"].sum().sort_values(ascending=False).reset_index()
        by.columns = ["Category", "Amount"]
        ui.bar_chart(by, "Category", "Amount", horizontal=True, height=max(220, 46 * len(by)))
        m = op.assign(month=pd.to_datetime(op["expense_date"]).dt.strftime("%Y-%m"))
        pivot = m.pivot_table(index="category", columns="month", values="amount", aggfunc="sum", fill_value=0)
        pivot["Total"] = pivot.sum(axis=1)
        pivot = pivot.sort_values("Total", ascending=False).reset_index()
        ui.table(ui.fmt(pivot, [c for c in pivot.columns if c != "category"]).rename(columns={"category": "Category"}))
