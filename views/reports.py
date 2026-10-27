import io

import pandas as pd
import streamlit as st

import db
import ui

ui.header("Reports", "Business reports — starting with sales by product")

section = ui.sections(["Sales By Products"], "report_tab")


def _excel_bytes(df):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Report")
    return buf.getvalue()


def _excel_bytes_multi(sheets):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for name, df in sheets:
            safe = str(name)[:31].replace("/", "-")
            df.to_excel(writer, index=False, sheet_name=safe)
    return buf.getvalue()


def _pdf_bytes(sections):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    elements = []
    for i, (title, df) in enumerate(sections):
        elements.append(Paragraph(title, styles["Title"]))
        elements.append(Spacer(1, 10))
        data = [list(df.columns)] + df.astype(str).values.tolist()
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ]))
        elements.append(table)
        if i < len(sections) - 1:
            elements.append(PageBreak())
    doc.build(elements)
    return buf.getvalue()


def _download_buttons(title, df, filename_base, key_base):
    c1, c2 = st.columns(2)
    c1.download_button(
        "Download Excel",
        data=_excel_bytes(df),
        file_name=filename_base + ".xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=key_base + "_xlsx",
        use_container_width=True,
    )
    c2.download_button(
        "Download PDF",
        data=_pdf_bytes([(title, df)]),
        file_name=filename_base + ".pdf",
        mime="application/pdf",
        key=key_base + "_pdf",
        use_container_width=True,
    )


if section == "Sales By Products":
    lines = db.get("invoice_lines", order="id")
    invoices = db.get("invoices", order="id")
    products = db.get("products", order="id")

    if lines.empty or invoices.empty or products.empty:
        st.info("No sales recorded yet.")
    else:
        h = lines.merge(invoices[["id", "invoice_date"]], left_on="invoice_id", right_on="id", suffixes=("", "_inv"))
        h = h.merge(products[["id", "name"]], left_on="product_id", right_on="id", suffixes=("", "_prod"))
        h["amount"] = h["qty"] * h["unit_rate"] - h["line_discount"]
        h["month_key"] = pd.to_datetime(h["invoice_date"]).dt.strftime("%Y-%m")
        h["Month"] = pd.to_datetime(h["month_key"] + "-01").dt.strftime("%b %Y")

        q = st.text_input("Search", placeholder="Search by product name or month, e.g. 'Aug' or '1500ml'", key="rep_search")
        qn = q.strip().lower()

        # ---------- All-time totals, product-wise ----------
        st.subheader("All-Time Totals — Product Wise")

        by_prod_all = h.groupby("name").agg(Quantity=("qty", "sum"), Amount=("amount", "sum")).reset_index()
        by_prod_all = by_prod_all.sort_values("Amount", ascending=False)

        if qn:
            filtered_all = by_prod_all[by_prod_all["name"].str.lower().str.contains(qn)]
        else:
            filtered_all = by_prod_all

        if filtered_all.empty:
            st.info("No products match your search.")
        else:
            disp_all = filtered_all.rename(columns={"name": "Product"})[["Product", "Quantity", "Amount"]]
            total_row = pd.DataFrame([{
                "Product": "TOTAL",
                "Quantity": filtered_all["Quantity"].sum(),
                "Amount": filtered_all["Amount"].sum(),
            }])
            disp_all = pd.concat([disp_all, total_row], ignore_index=True)
            disp_all_fmt = ui.fmt(disp_all, ["Quantity", "Amount"], 2)
            ui.table(disp_all_fmt)
            _download_buttons("All-Time Totals - Product Wise", disp_all_fmt, "all_time_totals", "alltime")

        st.markdown("---")

        # ---------- Month by month breakdown ----------
        st.subheader("Month by Month Breakdown")

        by_month = h.groupby(["month_key", "Month"]).agg(Quantity=("qty", "sum"), Amount=("amount", "sum")).reset_index()
        by_month = by_month.sort_values("month_key", ascending=False)
        by_prod = h.groupby(["month_key", "name"]).agg(Quantity=("qty", "sum"), Amount=("amount", "sum")).reset_index()

        shown_any = False
        for _, mrow in by_month.iterrows():
            mk, mlabel, mqty, mamt = mrow["month_key"], mrow["Month"], mrow["Quantity"], mrow["Amount"]
            prods = by_prod[by_prod["month_key"] == mk].sort_values("name")
            month_matches = (qn in mlabel.lower()) if qn else True

            if qn and not month_matches:
                prods = prods[prods["name"].str.lower().str.contains(qn)]
                if prods.empty:
                    continue

            shown_any = True
            label = mlabel + "   ·   Qty " + ui.money(mqty, 2) + "   ·   PKR " + ui.money(mamt, 2)
            with st.expander(label, expanded=bool(qn)):
                disp = prods.rename(columns={"name": "Product"})[["Product", "Quantity", "Amount"]]
                month_total_row = pd.DataFrame([{
                    "Product": "TOTAL",
                    "Quantity": prods["Quantity"].sum(),
                    "Amount": prods["Amount"].sum(),
                }])
                disp = pd.concat([disp, month_total_row], ignore_index=True)
                disp_fmt = ui.fmt(disp, ["Quantity", "Amount"], 2)
                ui.table(disp_fmt)
                _download_buttons(mlabel + " - Sales by Product", disp_fmt, "sales_" + mk, "month_" + mk)

        if not shown_any:
            st.info("No results match your search.")

        st.markdown("---")
        t1, t2 = st.columns(2)
        t1.metric("Total Quantity (All Months)", ui.money(float(h["qty"].sum()), 2))
        t2.metric("Total Amount (All Months, PKR)", ui.money(float(h["amount"].sum()), 2))
        st.caption("Amounts shown here are before whole-invoice discounts, so the total may differ slightly "
                   "from 'Net Sales' on the Dashboard if you've applied invoice-level discounts.")

        # ---------- Export full report (everything, ignoring search) ----------
        st.markdown("---")
        st.subheader("Export Full Report (All Months, All Products)")
        st.caption("These two buttons export everything, regardless of what you've searched above. "
                   "The buttons next to each table above only export that specific table.")

        full_all_time = by_prod_all.rename(columns={"name": "Product"})[["Product", "Quantity", "Amount"]]
        full_all_time_total = pd.DataFrame([{
            "Product": "TOTAL",
            "Quantity": by_prod_all["Quantity"].sum(),
            "Amount": by_prod_all["Amount"].sum(),
        }])
        full_all_time = pd.concat([full_all_time, full_all_time_total], ignore_index=True)
        full_all_time = ui.fmt(full_all_time, ["Quantity", "Amount"], 2)

        full_sections = [("All-Time Totals - Product Wise", full_all_time)]
        full_sheets = [("All-Time Totals", full_all_time)]

        for _, mrow in by_month.iterrows():
            mk, mlabel = mrow["month_key"], mrow["Month"]
            prods_full = by_prod[by_prod["month_key"] == mk].sort_values("name")
            disp_full = prods_full.rename(columns={"name": "Product"})[["Product", "Quantity", "Amount"]]
            total_full = pd.DataFrame([{
                "Product": "TOTAL",
                "Quantity": prods_full["Quantity"].sum(),
                "Amount": prods_full["Amount"].sum(),
            }])
            disp_full = pd.concat([disp_full, total_full], ignore_index=True)
            disp_full = ui.fmt(disp_full, ["Quantity", "Amount"], 2)
            full_sections.append((mlabel + " - Sales by Product", disp_full))
            full_sheets.append((mlabel, disp_full))

        c1, c2 = st.columns(2)
        c1.download_button(
            "Download Full Report — Excel (one tab per month)",
            data=_excel_bytes_multi(full_sheets),
            file_name="sales_by_products_full_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="full_xlsx",
            use_container_width=True,
        )
        c2.download_button(
            "Download Full Report — PDF (one page per month)",
            data=_pdf_bytes(full_sections),
            file_name="sales_by_products_full_report.pdf",
            mime="application/pdf",
            key="full_pdf",
            use_container_width=True,
        )
