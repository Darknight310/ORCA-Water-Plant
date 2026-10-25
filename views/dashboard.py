import pandas as pd
import plotly.express as px
import streamlit as st

import db
import ui

ui.header("Dashboard", "Profit, money owed to you, and stock at a glance")

pnl = db.get("v_pnl")
if pnl.empty:
    st.warning("No data found yet.")
    st.stop()
p = {k: float(v) for k, v in pnl.iloc[0].items()}

summ = db.get("v_invoice_summary", order="id")
raw = db.get("v_raw_stock", order="id")
fg = db.get("v_product_stock", order="id")

net = p["net_sales"]


def pct(x):
    return (x / net * 100) if net else 0.0


c1, c2, c3, c4 = st.columns(4)
c1.metric("Net sales", "PKR " + ui.money(net))
c2.metric("Gross margin", "PKR " + ui.money(p["gross_margin"]),
          f"{pct(p['gross_margin']):.1f}% of net sales", delta_color="off")
c3.metric("Operating profit", "PKR " + ui.money(p["operating_net_profit"]),
          f"{pct(p['operating_net_profit']):.1f}% of net sales", delta_color="off")
c4.metric("Retained profit", "PKR " + ui.money(p["net_retained_profit"]),
          "after owner draws", delta_color="off")

owed = 0.0
if not summ.empty:
    owed = float(summ.loc[summ["balance_due"] > 0, "balance_due"].sum())
raw_val = float(raw["stock_value"].sum()) if not raw.empty else 0.0
fg_val = float(fg["stock_value"].sum()) if not fg.empty else 0.0
low = []
if not raw.empty:
    low += raw.loc[raw["status"] == "LOW", "name"].tolist()
if not fg.empty:
    low += fg.loc[fg["status"] == "LOW", "name"].tolist()

d1, d2, d3, d4 = st.columns(4)
d1.metric("Customers owe you", "PKR " + ui.money(owed))
d2.metric("Raw material stock", "PKR " + ui.money(raw_val))
d3.metric("Finished goods stock", "PKR " + ui.money(fg_val))
d4.metric("Items running low", str(len(low)))

st.write("")
left, right = st.columns([3, 2], gap="large")

with left:
    st.markdown("#### Profit & loss")
    rows = [
        ("Gross sales", p["gross_sales"], "", ""),
        ("Less: discounts", -p["discounts"], "s", ""),
        ("Net sales", p["net_sales"], "t", ""),
        ("Less: cost of goods sold", -p["cogs"], "s", ""),
        ("Gross margin", p["gross_margin"], "t", ""),
        ("Less: damage & wastage", -p["damage_loss"], "s", ""),
        ("Less: operating expenses", -p["operating_expenses"], "s", ""),
        ("Operating net profit", p["operating_net_profit"], "t", ""),
        ("Less: owner draws", -p["owner_draws"], "s", ""),
        ("Retained profit", p["net_retained_profit"], "t", ""),
    ]
    html = "<table class='pl'>"
    for label, val, cls, _ in rows:
        shown = ui.money(val, 2) if val >= 0 else "(" + ui.money(-val, 2) + ")"
        html += ("<tr class='" + cls + "'><td>" + label + "</td><td class='n'>" + shown +
                 "</td><td class='p'>" + f"{pct(val):.1f}%" + "</td></tr>")
    html += "</table>"
    st.markdown("<div class='card'>" + html + "</div>", unsafe_allow_html=True)

with right:
    st.markdown("#### Where net sales went")
    parts = {
        "Cost of goods": max(p["cogs"], 0),
        "Damage & wastage": max(p["damage_loss"], 0),
        "Operating expenses": max(p["operating_expenses"], 0),
        "Owner draws": max(p["owner_draws"], 0),
        "Retained profit": max(p["net_retained_profit"], 0),
    }
    if sum(parts.values()) > 0:
        fig = px.pie(names=list(parts.keys()), values=list(parts.values()), hole=0.6,
                     color_discrete_sequence=ui.PALETTE)
        fig.update_traces(textinfo="percent", sort=False)
        ui.chart(fig)
    else:
        st.info("The chart appears once you have sales.")

st.write("")
a, b = st.columns(2, gap="large")
with a:
    st.markdown("#### Net sales by month")
    if summ.empty:
        st.info("No invoices yet.")
    else:
        m = summ.assign(month=pd.to_datetime(summ["invoice_date"]).dt.strftime("%Y-%m"))
        m = m.groupby("month")["net_amount"].sum()
        st.bar_chart(m, color=ui.ACCENT)
with b:
    st.markdown("#### Who owes you the most")
    if summ.empty or owed == 0:
        st.success("Nobody owes you anything.")
    else:
        top = summ[summ["balance_due"] > 0].groupby("customer_name")["balance_due"].sum()
        top = top.sort_values(ascending=False).head(6).reset_index()
        top.columns = ["Customer", "Balance due (PKR)"]
        ui.table(ui.fmt(top, ["Balance due (PKR)"]))

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
             ". Check opening stock (Stock & Production → physical count).")
if not low and not negative:
    st.caption("Tip: set alert levels in Stock & Production to get low-stock warnings here.")
