import datetime as dt
import io

import pandas as pd
import streamlit as st

import db
import ui

ui.header("Reports", "Investor-ready profit reports and sales breakdowns")

PNL_SECTION = "Profit and Loss Using Cost of Goods Sold"
section = ui.sections([PNL_SECTION, "Sales By Products"], "report_tab")


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


def _display_frame(df, percent_cols=()):
    """Formatted copy for screens/PDFs; downloads keep the numeric originals."""
    out = df.copy()
    percent_cols = set(percent_cols)
    numeric = [c for c in out.columns
               if c not in percent_cols and pd.api.types.is_numeric_dtype(out[c])]
    out = ui.fmt(out, numeric, 2)
    for col in percent_cols:
        if col in out.columns:
            out[col] = out[col].map(
                lambda v: "" if pd.isna(v) else f"{float(v):,.2f}%")
    return out


def _append_total(df, label_col):
    if df.empty:
        return df.copy()
    total = {col: "" for col in df.columns}
    total[label_col] = "TOTAL"
    for col in df.columns:
        if col != label_col and pd.api.types.is_numeric_dtype(df[col]):
            total[col] = float(df[col].sum())
    return pd.concat([df, pd.DataFrame([total])], ignore_index=True)


def _expense_with_subtotals(df, net_sales):
    if df.empty:
        return df.copy()
    rows = []
    for type_name in ("Operating Expense", "Owner Draw"):
        part = df[df["Type"] == type_name]
        if part.empty:
            continue
        rows.append(part)
        amount = float(part["Amount (PKR)"].sum())
        rows.append(pd.DataFrame([{
            "Type": type_name,
            "Category": "TOTAL",
            "Entries": int(part["Entries"].sum()),
            "Amount (PKR)": amount,
            "% of Net Sales": (amount / net_sales * 100.0) if net_sales else 0.0,
            "% of Type Total": 100.0,
        }]))
    return pd.concat(rows, ignore_index=True) if rows else df.copy()


def _pnl_excel_bytes(sheets, period_label, prepared_label):
    """Investor workbook: titled sheets, frozen headers and real numeric cells."""
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    title = "ORCA Water Plant — Profit and Loss Using Cost of Goods Sold"
    bold_labels = {
        "Net Sales", "Gross Profit", "Total Operating Expenses", "Overall Profit",
        "Current Profit (Profit Retained in Business)", "TOTAL",
    }
    header_fill = PatternFill("solid", fgColor="17365D")
    subtotal_fill = PatternFill("solid", fgColor="DCE6F1")
    thin = Side(style="thin", color="B7C3D0")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for sheet_name, df in sheets:
            safe = str(sheet_name)[:31].replace("/", "-")
            df.to_excel(writer, index=False, sheet_name=safe, startrow=3)
            ws = writer.sheets[safe]
            last_col = max(len(df.columns), 1)
            ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last_col)
            ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=last_col)
            ws["A1"] = title
            ws["A1"].font = Font(name="Calibri", size=14, bold=True, color="17365D")
            ws["A2"] = f"Period: {period_label}  |  Prepared: {prepared_label}  |  Sheet: {sheet_name}"
            ws["A2"].font = Font(name="Calibri", size=9, italic=True, color="595959")
            ws.row_dimensions[1].height = 20
            ws.row_dimensions[2].height = 15
            ws.freeze_panes = "A5"
            ws.sheet_properties.pageSetUpPr.fitToPage = True
            ws.page_setup.orientation = "landscape"
            ws.page_setup.fitToWidth = 1
            ws.page_setup.fitToHeight = 0
            if not df.empty and not sheet_name.startswith("Notes"):
                ws.auto_filter.ref = f"A4:{get_column_letter(last_col)}{4 + len(df)}"

            for col_idx, col_name in enumerate(df.columns, start=1):
                header = ws.cell(row=4, column=col_idx)
                header.fill = header_fill
                header.font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
                header.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                header.border = border

                values = [str(col_name)] + [str(v) for v in df[col_name].tolist()]
                if sheet_name.startswith("Notes"):
                    width = 115
                elif col_idx == 1:
                    width = min(max(18, max(len(v) for v in values) + 2), 58)
                else:
                    width = min(max(14, max(len(v) for v in values) + 2), 28)
                ws.column_dimensions[get_column_letter(col_idx)].width = width

            for row_idx, (_, row) in enumerate(df.iterrows(), start=5):
                is_bold = ((str(row.iloc[0]) in bold_labels) or
                           ("TOTAL" in [str(v) for v in row.tolist()])) if len(row) else False
                if sheet_name.startswith("Notes"):
                    ws.row_dimensions[row_idx].height = 32
                for col_idx, col_name in enumerate(df.columns, start=1):
                    cell = ws.cell(row=row_idx, column=col_idx)
                    cell.border = border
                    cell.font = Font(name="Calibri", size=10, bold=is_bold)
                    if is_bold:
                        cell.fill = subtotal_fill
                    if isinstance(cell.value, (int, float)) and not isinstance(cell.value, bool):
                        cell.alignment = Alignment(horizontal="right", vertical="center")
                        if "%" in str(col_name):
                            cell.number_format = '0.00"%"'
                        elif "Entries" in str(col_name):
                            cell.number_format = '#,##0'
                        else:
                            cell.number_format = '#,##0.00'
                    else:
                        cell.alignment = Alignment(
                            horizontal="left", vertical="center",
                            wrap_text=bool(sheet_name.startswith("Notes") or col_idx == 1))
    return buf.getvalue()


def _pnl_pdf_bytes(period_label, prepared_label, sections, notes):
    """Landscape investor PDF with the statement and supporting schedules."""
    from xml.sax.saxutils import escape

    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    bold_labels = {
        "Net Sales", "Gross Profit", "Total Operating Expenses", "Overall Profit",
        "Current Profit (Profit Retained in Business)", "TOTAL",
    }

    def make_table(df, widths, font_size=7):
        data = [list(df.columns)] + df.astype(str).values.tolist()
        commands = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), font_size),
            ("LEADING", (0, 0), (-1, -1), font_size + 2),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B7C3D0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F6FA")]),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
        for idx, row_values in enumerate(df.astype(str).values.tolist() if not df.empty else [], start=1):
            if (row_values and row_values[0] in bold_labels) or "TOTAL" in row_values:
                commands += [
                    ("FONTNAME", (0, idx), (-1, idx), "Helvetica-Bold"),
                    ("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#DCE6F1")),
                ]
        table = Table(data, colWidths=widths, repeatRows=1)
        table.setStyle(TableStyle(commands))
        return table

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawString(1.2 * cm, 0.75 * cm,
                          "ORCA Water Plant | Profit and Loss Using Cost of Goods Sold | " + period_label)
        canvas.drawRightString(28.5 * cm, 0.75 * cm, f"Page {doc.page}")
        canvas.restoreState()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4), leftMargin=1.2 * cm, rightMargin=1.2 * cm,
        topMargin=1.1 * cm, bottomMargin=1.2 * cm,
        title="ORCA Water Plant — Profit and Loss Using Cost of Goods Sold",
        author="ORCA Water Plant")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="InvestorTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=19, leading=22, textColor=colors.HexColor("#17365D"), alignment=TA_CENTER))
    styles.add(ParagraphStyle(
        name="InvestorSubTitle", parent=styles["Normal"], fontName="Helvetica",
        fontSize=9, leading=12, textColor=colors.HexColor("#475569"), alignment=TA_CENTER))
    styles.add(ParagraphStyle(
        name="InvestorHeading", parent=styles["Heading1"], fontName="Helvetica-Bold",
        fontSize=13, leading=16, textColor=colors.HexColor("#17365D"), spaceBefore=8, spaceAfter=6))
    styles.add(ParagraphStyle(
        name="InvestorBody", parent=styles["Normal"], fontName="Helvetica",
        fontSize=8.5, leading=12, textColor=colors.HexColor("#1F2937")))

    elements = [
        Paragraph("ORCA Water Plant", styles["InvestorTitle"]),
        Paragraph("Profit and Loss Using Cost of Goods Sold", styles["InvestorTitle"]),
        Paragraph(f"Period: {escape(period_label)} &nbsp; | &nbsp; Prepared: {escape(prepared_label)}",
                  styles["InvestorSubTitle"]),
        Spacer(1, 8),
        Paragraph("COGS is the actual production-batch cost locked onto each sold invoice line. "
                  "Raw-material purchases are stock until the goods made from them are sold or damaged.",
                  styles["InvestorSubTitle"]),
        Spacer(1, 10),
    ]
    for i, (heading, df, widths, font_size) in enumerate(sections):
        if i:
            elements.append(PageBreak())
        elements.append(Paragraph(escape(heading), styles["InvestorHeading"]))
        elements.append(make_table(df, widths, font_size))
    elements.append(PageBreak())
    elements.append(Paragraph("Notes & Basis of Preparation", styles["InvestorHeading"]))
    for note in notes:
        elements.append(Paragraph("• " + escape(note), styles["InvestorBody"]))
        elements.append(Spacer(1, 5))

    doc.build(elements, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()


if section == PNL_SECTION:
    invoices = db.get("invoices", order="id")
    invoice_lines = db.get("invoice_lines", order="id")
    products = db.get("products", order="id")
    damages = db.get("damages", order="id")
    expenses = db.get("expenses", order="id")

    date_values = []
    for frame, col in ((invoices, "invoice_date"), (damages, "damage_date"),
                       (expenses, "expense_date")):
        if frame is not None and not frame.empty and col in frame.columns:
            vals = pd.to_datetime(frame[col], errors="coerce").dropna()
            if not vals.empty:
                date_values += [vals.min(), vals.max()]

    st.subheader(PNL_SECTION)
    st.caption("Investor-ready statement using the actual batch cost locked onto each sold invoice line. "
               "Raw-material purchases stay in stock value and do not reduce profit until the goods made "
               "from them are sold or damaged.")

    if not date_values:
        st.info("No dated sales, damage or expense records are available yet.")
    else:
        data_start = min(date_values).date()
        data_end = max(date_values).date()
        today = dt.date.today()
        today_ts = pd.Timestamp(today)
        current_first = today_ts.replace(day=1)
        current_last = current_first + pd.offsets.MonthEnd(0)
        previous_last = current_first - pd.Timedelta(days=1)
        previous_first = previous_last.replace(day=1)

        p1, p2, p3 = st.columns(3)
        period_choice = p1.selectbox(
            "Report Period",
            ["All Time", "Current Month", "Previous Month", "Custom Dates"],
            key="pnl_period_choice")
        if period_choice == "All Time":
            start_date, end_date = data_start, data_end
            p2.metric("From", start_date.strftime("%d %b %Y"))
            p3.metric("To", end_date.strftime("%d %b %Y"))
        elif period_choice == "Current Month":
            start_date, end_date = current_first.date(), current_last.date()
            p2.metric("From", start_date.strftime("%d %b %Y"))
            p3.metric("To", end_date.strftime("%d %b %Y"))
        elif period_choice == "Previous Month":
            start_date, end_date = previous_first.date(), previous_last.date()
            p2.metric("From", start_date.strftime("%d %b %Y"))
            p3.metric("To", end_date.strftime("%d %b %Y"))
        else:
            start_date = p2.date_input("From", value=data_start, key="pnl_start")
            end_date = p3.date_input("To", value=data_end, key="pnl_end")

        if start_date > end_date:
            st.error("The From date must be on or before the To date.")
        else:
            period_label = f"{start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}"
            if period_choice == "All Time":
                period_label = "All Time (" + period_label + ")"
            prepared_label = today.strftime("%d %b %Y")
            report = db.profit_loss_report(
                invoices, invoice_lines, products, damages, expenses, start_date, end_date)
            s = report["summary"]
            statement = report["statement"]
            product_schedule = report["product_schedule"].copy()
            monthly = report["monthly"].copy()
            expense_schedule = report["expense_schedule"].copy()

            r1, r2, r3 = st.columns(3)
            with r1:
                ui.tile("rpnl_net", "Net Sales", "PKR " + ui.money(s["net_sales"], 2), "Period total", "views/reports.py", important=True)
            with r2:
                ui.tile("rpnl_cogs", "COGS", "PKR " + ui.money(s["cogs"], 2), "Cost of goods sold", "views/reports.py")
            with r3:
                ui.tile("rpnl_gp", "Gross Profit", "PKR " + ui.money(s["gross_profit"], 2), "Net Sales − COGS", "views/stock.py")

            st.write("")

            n1, n2 = st.columns(2)
            with n1:
                ui.tile("rpnl_op", "Overall Profit", "PKR " + ui.money(s["overall_profit"], 2), "After operating expenses", "views/expenses.py")
            with n2:
                ui.tile("rpnl_cp", "Current Profit", "PKR " + ui.money(s["current_profit"], 2), "After owner draws", "views/expenses.py", important=True)
            st.caption(
                f"Period: {period_label}  ·  Invoices: {s['invoice_count']}  ·  "
                f"Bundles sold: {ui.money(s['bundles_sold'], 2)}  ·  "
                f"Gross margin: {s['gross_margin_pct']:.2f}%  ·  "
                f"Current profit margin: {s['current_profit_pct']:.2f}%")

            statement_export = statement.drop(columns=["Row Type"], errors="ignore")
            product_export = _append_total(product_schedule, "Product")
            if not product_export.empty:
                last = product_export.index[-1]
                sales_after = float(product_export.loc[last, "Sales After Line Discounts (PKR)"])
                gp = float(product_export.loc[last, "Gross Profit Before Whole-Invoice Discounts (PKR)"])
                product_export.loc[last, "Gross Margin %"] = (gp / sales_after * 100.0) if sales_after else 0.0
            monthly_export = _append_total(monthly, "Month")
            expense_export = _expense_with_subtotals(expense_schedule, s["net_sales"])

            bundles = s["bundles_sold"]
            key_figures = pd.DataFrame([
                {"Metric": "Invoices in Period", "Value": float(s["invoice_count"]), "Unit": "invoices"},
                {"Metric": "Bundles Sold", "Value": float(bundles), "Unit": "bundles"},
                {"Metric": "Net Sales Per Bundle", "Value": (s["net_sales"] / bundles if bundles else 0.0), "Unit": "PKR"},
                {"Metric": "COGS Per Bundle", "Value": (s["cogs"] / bundles if bundles else 0.0), "Unit": "PKR"},
                {"Metric": "Gross Profit Per Bundle", "Value": (s["gross_profit"] / bundles if bundles else 0.0), "Unit": "PKR"},
                {"Metric": "Gross Margin", "Value": float(s["gross_margin_pct"]), "Unit": "% of Net Sales"},
                {"Metric": "Overall Profit Margin", "Value": float(s["overall_profit_pct"]), "Unit": "% of Net Sales"},
                {"Metric": "Current Profit Margin", "Value": float(s["current_profit_pct"]), "Unit": "% of Net Sales"},
            ])
            notes = [
                f"Reporting period: {period_label}. Prepared from the live ORCA Water Plant records on {prepared_label}.",
                "Cost of Goods Sold (COGS) is taken from invoice_lines.cogs_amount — the actual production-batch cost locked onto each invoice line when the goods were sold. It is not calculated from the current average raw-material cost.",
                "Raw-material purchases are treated as stock when bought. A purchase by itself does not reduce Gross Profit, Overall Profit or Current Profit; its cost reaches profit later through COGS when finished goods are sold, or through Damage & Wastage if stock is damaged.",
                "Production consumes raw-material batches oldest first (FIFO), and sales consume finished-goods production batches oldest first. The exact batches and costs are retained in the batch-usage records.",
                "Damage & Wastage is valued at the recorded batch cost at the time of damage.",
                "Operating Expenses include plant expenses recorded as OPERATING. Owner Draws are shown after Overall Profit because they are owner withdrawals, not plant operating expenses.",
                f"The product schedule is after line discounts and before whole-invoice discounts of PKR {ui.money(s['whole_invoice_discounts'], 2)}; the main statement includes all discounts.",
                "Percentages in the main statement are calculated as a percentage of Net Sales. Amounts are in Pakistani Rupees (PKR), subject to rounding.",
            ]
            notes_df = pd.DataFrame({"Notes & Basis of Preparation": notes})

            statement_display = _display_frame(statement_export, ["% of Net Sales"])
            product_display = _display_frame(product_export, ["Gross Margin %"])
            monthly_display = _display_frame(monthly_export)
            expense_display = _display_frame(expense_export, ["% of Net Sales", "% of Type Total"])
            key_figures_display = _display_frame(key_figures)

            excel_sheets = [
                ("P&L Statement", statement_export),
                ("Key Figures", key_figures),
                ("Product Sales & COGS", product_export),
                ("Monthly P&L", monthly_export),
                ("Expense Breakdown", expense_export),
                ("Notes & Basis", notes_df),
            ]
            from reportlab.lib.units import cm as _cm
            pdf_sections = [
                ("Profit & Loss Statement", statement_display,
                 [13 * _cm, 5 * _cm, 5 * _cm], 8),
                ("Key Figures", key_figures_display,
                 [10 * _cm, 5 * _cm, 6 * _cm], 8),
            ]
            if not product_display.empty:
                pdf_sections.append((
                    "Product Sales and COGS", product_display,
                    [4.8 * _cm, 2.4 * _cm, 3.1 * _cm, 3.0 * _cm,
                     3.7 * _cm, 3.0 * _cm, 4.2 * _cm, 2.6 * _cm], 6.7))
            if not monthly_display.empty:
                pdf_sections.append((
                    "Monthly Profit & Loss", monthly_display,
                    [2.5 * _cm] + [2.45 * _cm] * 10, 6.2))
            if not expense_display.empty:
                pdf_sections.append((
                    "Expense and Owner Draw Breakdown", expense_display,
                    [4.2 * _cm, 5.2 * _cm, 2.2 * _cm, 4.0 * _cm,
                     4.0 * _cm, 4.0 * _cm], 7))

            file_base = f"ORCA_Profit_and_Loss_COGS_{start_date.isoformat()}_to_{end_date.isoformat()}"
            d1, d2 = st.columns(2)
            d1.download_button(
                "Download Investor P&L — Excel",
                data=_pnl_excel_bytes(excel_sheets, period_label, prepared_label),
                file_name=file_base + ".xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"pnl_xlsx_{start_date}_{end_date}",
                use_container_width=True)
            d2.download_button(
                "Download Investor P&L — PDF",
                data=_pnl_pdf_bytes(period_label, prepared_label, pdf_sections, notes),
                file_name=file_base + ".pdf",
                mime="application/pdf",
                key=f"pnl_pdf_{start_date}_{end_date}",
                use_container_width=True)

            pnl_rows = []
            for _, row in statement.iterrows():
                label = str(row["Particulars"])
                display_label = label
                if label.startswith("Operating Expense — "):
                    display_label = "&nbsp;&nbsp;&nbsp;• " + label.replace("Operating Expense — ", "")
                if label == "Current Profit (Profit Retained in Business)":
                    label_colour = amount_colour = percent_colour = "blue"
                elif label in ("Net Sales", "Gross Profit", "Overall Profit"):
                    label_colour = "ink"
                    amount_colour = "green" if label != "Gross Profit" else "cyan"
                    percent_colour = amount_colour
                elif "Cost of Goods Sold" in label:
                    label_colour = amount_colour = percent_colour = "rose"
                elif "Owner Draws" in label:
                    label_colour = amount_colour = percent_colour = "purple"
                elif float(row["Amount (PKR)"]) < 0:
                    label_colour = amount_colour = percent_colour = "amber"
                else:
                    label_colour = amount_colour = percent_colour = "ink"
                pnl_rows.append((
                    display_label, float(row["Amount (PKR)"]), float(row["% of Net Sales"]),
                    label_colour, amount_colour, percent_colour,
                    str(row["Row Type"]) in ("Subtotal", "Total")))
            ui.pnl_table(pnl_rows, title=PNL_SECTION, badge="Investor Report")

            st.markdown("---")
            st.subheader("Product Sales and COGS")
            if product_display.empty:
                st.info("No product sales in this period.")
            else:
                ui.table(product_display)
                st.caption("Product gross profit is before whole-invoice discounts of PKR " +
                           ui.money(s["whole_invoice_discounts"], 2) +
                           ". The main statement above includes those discounts in Net Sales.")

            st.markdown("---")
            st.subheader("Monthly Profit & Loss")
            if monthly_display.empty:
                st.info("No dated profit or loss activity in this period.")
            else:
                ui.table(monthly_display)

            st.markdown("---")
            st.subheader("Expense and Owner Draw Breakdown")
            if expense_display.empty:
                st.info("No operating expenses or owner draws in this period.")
            else:
                ui.table(expense_display)

            with st.expander("Notes & Basis of Preparation"):
                for note in notes:
                    st.markdown("- " + note)

elif section == "Sales By Products":
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
