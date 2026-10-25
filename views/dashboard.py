import pandas as pd
import plotly.express as px
import streamlit as st

import db
import ui

ui.header("Dashboard", "Profit, receivables and stock at a glance. Click any tile to open its page.")

pnl = db.get("v_pnl")
if pnl.empty:
    st.warning("No data found yet.")
    st.stop()
p = {k: float(v) for k, v in pnl.iloc[0].items()}

summ = db.get("v_invoice_summary", order="id")
raw = db.get("v_raw_stock", order="id")
fg = db.get("v_product_stock", order="id")

SALES, STOCK, EXPENSES = "views/sales.py", "views/stock.py", "views/expenses.py"
net = p["net_sales"]


def pct(x):
    return (x / net * 100) if net else 0.0


owed, open_count = 0.0, 0
if not summ.empty:
    owed = float(summ.loc[summ["balance_due"] > 0, "balance_due"].sum())
    open_count = int((summ["balance_due"] > 0).sum())
raw_val = float(raw["stock_value"].sum()) if not raw.empty else 0.0
fg_val = float(fg["stock_value"].sum()) if not fg.empty else 0.0
bundles = float(fg["balance"].sum()) if not fg.empty else 0.0
low = []
if not raw.empty:
    low += raw.loc[raw["status"] == "LOW", "name"].tolist()
if not fg.empty:
    low += fg.loc[fg["status"] == "LOW", "name"].tolist()
levels_set = False
if not raw.empty and (raw["status"] != "Set level").any():
    levels_set = True
if not fg.empty and (fg["status"] != "Set level").any():
    levels_set = True

c1, c2, c3, c4 = st.columns(4)
with c1:
    ui.tile("net", "Net Sales", "PKR " + ui.money(net), "Gross Sales PKR " + ui.money(p["gross_sales"]), SALES)
with c2:
    ui.tile("gp", "Gross Profit", "PKR " + ui.money(p["gross_margin"]), f"{pct(p['gross_margin']):.1f}% Of Net Sales", STOCK)
with c3:
    ui.tile("op", "Overall Profit", "PKR " + ui.money(p["operating_net_profit"]), f"{pct(p['operating_net_profit']):.1f}% Of Net Sales", EXPENSES)
with c4:
    ui.tile("cp", "Current Profit", "PKR " + ui.money(p["net_retained_profit"]), "After Owner Draws", EXPENSES)

st.write("")
d1, d2, d3, d4 = st.columns(4)
with d1:
    ui.tile("recv", "Balance Receivable", "PKR " + ui.money(owed), str(open_count) + " Open Invoices", SALES)
with d2:
    ui.tile("raw", "Raw Material Stock Value", "PKR " + ui.money(raw_val), str(len(raw)) + " Items", STOCK)
with d3:
    ui.tile("fg", "Finished Goods Stock Value", "PKR " + ui.money(fg_val), ui.money(bundles) + " Bundles In Stock", STOCK)
with d4:
    sub = "Needs Attention" if low else ("All Stock Healthy" if levels_set else "Set Alert Levels In Stock")
    ui.tile("low", "Items Running Low", str(len(low)), sub, STOCK)

st.write("")
left, right = st.columns([3, 2], gap="large")

with left:
    st.markdown("#### Profit & Loss")
    ui.pnl_table([
        ("Gross Sales", p["gross_sales"], pct(p["gross_sales"]), "ink", "ink", "muted", False),
        ("Discounts", -p["discounts"], pct(-p["discounts"]), "amber", "amber", "amber", False),
        ("Net Sales", p["net_sales"], pct(p["net_sales"]), "green", "green", "green", True),
        ("Cost Of Goods Sold (COGS)", -p["cogs"], pct(-p["cogs"]), "rose", "rose", "rose", False),
        ("Gross Profit", p["gross_margin"], pct(p["gross_margin"]), "ink", "cyan", "ink", True),
        ("Damage & Wastage", -p["damage_loss"], pct(-p["damage_loss"]), "amber", "amber", "amber", False),
        ("Operating Expenses", -p["operating_expenses"], pct(-p["operating_expenses"]), "amber", "amber", "amber", False),
        ("Overall Profit", p["operating_net_profit"], pct(p["operating_net_profit"]), "ink", "green", "ink", True),
        ("Owner Draws", -p["owner_draws"], pct(-p["owner_draws"]), "purple", "purple", "purple", False),
        ("Current Profit", p["net_retained_profit"], pct(p["net_retained_profit"]), "blue", "blue", "blue", True),
    ])

with right:
    st.markdown("#### Net Sales")
    parts = {
        "Cost Of Goods": max(p["cogs"], 0),
        "Damage & Wastage": max(p["damage_loss"], 0),
        "Operating Expenses": max(p["operating_expenses"], 0),
        "Owner Draws": max(p["owner_draws"], 0),
        "Current Profit": max(p["net_retained_profit"], 0),
    }
    if sum(parts.values()) > 0:
        fig = px.pie(names=list(parts.keys()), values=list(parts.values()), hole=0.62,
                     color_discrete_sequence=ui.PALETTE)
        fig.update_traces(textinfo="percent", sort=False, marker=dict(line=dict(width=0)))
        ui.chart(fig)
    else:
        st.info("The chart appears once you have sales.")

st.write("")
a, b = st.columns(2, gap="large")
with a:
    st.markdown("#### Net Sales By Month")
    if summ.empty:
        st.info("No invoices yet.")
    else:
        m = summ.assign(month=pd.to_datetime(summ["invoice_date"]).dt.strftime("%Y-%m"))
        m = m.groupby("month")["net_amount"].sum().reset_index().sort_values("month")
        m["Month"] = pd.to_datetime(m["month"] + "-01").dt.strftime("%b %Y")
        m = m.rename(columns={"net_amount": "Net Sales"})[["Month", "Net Sales"]]
        ui.bar_chart(m, "Month", "Net Sales")
with b:
    st.markdown("#### Balance Receivable By Customers")
    if summ.empty or owed == 0:
        st.success("Nobody owes you anything.")
    else:
        top = summ[summ["balance_due"] > 0].groupby("customer_name")["balance_due"].sum()
        top = top.sort_values(ascending=False).head(8).reset_index()
        top.columns = ["Customer", "Balance Receivable (PKR)"]
        ui.table(ui.fmt(top, ["Balance Receivable (PKR)"]))

st.write("")
if low:
    st.warning("Running low: " + ", ".join(low))
negative = []
if not raw.empty:
    negative += raw.loc[raw["balance"] < 0, "name"].tolist()
if not fg.empty:
    negative += fg.loc[fg["balance"] < 0, "name"].tolist()
if negative:
    st.error("Negative stock for: " + ", ".join(negative) +
             ". Check opening stock (Stock & Production, Physical Count).")
