# ==========================================
# 1. EXECUTIVE DASHBOARD
# ==========================================
if app_mode == "📊 Executive Dashboard":
    # Top KPI Metrics Row 1
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Gross Sales", value="PKR 192,320.00", delta="142 Invoiced Orders")
    with col2:
        st.metric(label="Total Discounts", value="PKR 6,190.00", delta="Rate Adjustments")
    with col3:
        st.metric(label="Net Sales Revenue", value="PKR 186,130.00", delta="Fully Reconciled")
    with col4:
        st.metric(label="Net Profit / Cash Flow", value="PKR 17,966.46", delta="After Draws & Expenses")

    # Top KPI Metrics Row 2
    col5, col6, col7 = st.columns(3)
    with col5:
        st.metric(label="Cost of Goods Sold (COGS)", value="PKR 136,053.54")
    with col6:
        st.metric(label="Direct Operating Expenses", value="PKR 11,760.00")
    with col7:
        st.metric(label="Owner Draws", value="PKR 20,350.00")

    st.markdown("---")
    
    # 2-Column Balanced Layout
    col_left, col_right = st.columns([3, 2], gap="large")
    
    with col_left:
        st.markdown("### 📋 Master Profit & Loss Breakdown")
        pnl_data = {
            "Financial Category": [
                "Gross Sales Revenue", "Less: Total Discounts Allowed", "Net Sales Revenue",
                "Less: Cost of Goods Sold (COGS)", "Gross Profit", "Less: Direct Operating Expenses",
                "Operating Net Profit", "Less: Owner Personal Draws", "FINAL NET CASH FLOW"
            ],
            "Amount (PKR)": [
                "192,320.00", "-6,190.00", "186,130.00", 
                "-136,053.54", "50,076.46", "-11,760.00", 
                "38,316.46", "-20,350.00", "17,966.46"
            ],
            "% of Revenue": [
                "103.3%", "-3.3%", "100.0%", "-73.1%", "26.9%", "-6.3%", "20.6%", "-10.9%", "9.6%"
            ]
        }
        st.dataframe(pd.DataFrame(pnl_data), use_container_width=True, hide_index=True)

    with col_right:
        st.markdown("### 📊 Cost & Expense Breakdown")
        st.markdown("<p style='color: #94A3B8; font-size: 0.85rem; margin-top: -10px;'>Visual allocation of plant capital outflows.</p>", unsafe_allow_html=True)
        
        # Spacer to align chart lower beside/down the table
        st.markdown("<br>", unsafe_allow_html=True)
        
        chart_data = pd.DataFrame({
            "Category": ["COGS", "Operating Expenses", "Owner Draws", "Net Profit"],
            "Amount": [136053.54, 11760.00, 20350.00, 17966.46]
        })
        
        fig = px.pie(
            chart_data, 
            values="Amount", 
            names="Category", 
            hole=0.55, 
            color_discrete_sequence=["#38BDF8", "#FBBF24", "#C084FC", "#34D399"]
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", 
            plot_bgcolor="rgba(0,0,0,0)", 
            font_color="#FFFFFF", 
            height=340,
            margin=dict(t=10, b=10, l=10, r=10), 
            legend=dict(orientation="h", y=-0.15, x=0.1)
        )
        st.plotly_chart(fig, use_container_width=True)
