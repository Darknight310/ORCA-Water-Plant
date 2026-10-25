import pandas as pd
import streamlit as st

import db

ACCENT = "#0E7490"
PALETTE = ["#0E7490", "#F59E0B", "#E11D48", "#7C3AED", "#10B981"]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
.stApp, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p, .stApp label,
.stApp input, .stApp textarea, .stApp button { font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif; }
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1280px; }
.pg-title { font-size: 1.9rem; font-weight: 800; letter-spacing: -0.03em; line-height: 1.1; }
.pg-sub { opacity: .6; margin: .3rem 0 1.5rem 0; font-size: .95rem; }
[data-testid="stMetric"] { background: rgba(127,127,127,.07); border: 1px solid rgba(127,127,127,.18);
  padding: 16px 18px; border-radius: 16px; }
[data-testid="stMetricLabel"] p { font-size: .75rem; font-weight: 600; text-transform: uppercase; letter-spacing: .05em; opacity: .7; }
[data-testid="stMetricValue"] { font-weight: 800; letter-spacing: -0.02em; }
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button { border-radius: 10px; font-weight: 600; padding: .5rem 1.1rem; }
[data-baseweb="tab-list"] { gap: 6px; }
[data-baseweb="tab"] { font-weight: 600; }
[data-testid="stSidebar"] { border-right: 1px solid rgba(127,127,127,.15); }
[data-testid="stSidebarNav"]::before { content: "\\1F4A7  ORCA WATER"; display: block; font-weight: 800;
  letter-spacing: .08em; padding: 1.1rem 1rem .4rem; font-size: 1rem; color: #0E7490; }
[data-testid="stExpander"] { border-radius: 12px; }
.card { background: rgba(127,127,127,.07); border: 1px solid rgba(127,127,127,.18); border-radius: 16px; padding: 18px 20px; }
.pl { width: 100%; border-collapse: collapse; font-size: .93rem; }
.pl td { padding: .62rem .6rem; border-bottom: 1px solid rgba(127,127,127,.15); }
.pl td.n { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.pl td.p { text-align: right; opacity: .55; width: 70px; }
.pl tr.t td { font-weight: 700; background: rgba(14,116,144,.09); }
.pl tr.s td:first-child { padding-left: 1.4rem; opacity: .85; }
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def header(title, subtitle=""):
    st.markdown(
        '<div class="pg-title">' + title + '</div><div class="pg-sub">' + subtitle + '</div>',
        unsafe_allow_html=True,
    )
    msg = st.session_state.pop("flash", None)
    if msg:
        st.success(msg, icon="✅")


def money(x, d=0):
    try:
        return f"{float(x):,.{d}f}"
    except (TypeError, ValueError):
        return "-"


def fmt(df, cols, d=0):
    out = df.copy()
    for c in cols:
        if c in out.columns:
            out[c] = out[c].map(lambda v: "" if pd.isna(v) else f"{float(v):,.{d}f}")
    return out


def table(df, **kw):
    try:
        st.dataframe(df, width="stretch", hide_index=True, **kw)
    except Exception:
        st.dataframe(df, use_container_width=True, hide_index=True, **kw)


def chart(fig):
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(t=10, b=10, l=10, r=10), height=320,
                      legend=dict(orientation="h", y=-0.1))
    try:
        st.plotly_chart(fig, width="stretch")
    except Exception:
        st.plotly_chart(fig, use_container_width=True)


def delete_entry(table_name, df, label_fn, key):
    """Small 'delete a wrong entry' box under a history table."""
    if df is None or df.empty:
        return
    with st.expander("Delete a wrong entry"):
        options = {}
        for _, r in df.iterrows():
            options["#" + str(int(r["id"])) + "  ·  " + label_fn(r)] = int(r["id"])
        choice = st.selectbox("Entry", list(options.keys()), index=None,
                              placeholder="Choose the entry to remove", key="del_pick_" + key)
        sure = st.checkbox("Yes, delete it permanently", key="del_sure_" + key)
        if st.button("Delete entry", key="del_btn_" + key, disabled=not (choice and sure)):
            try:
                db.delete(table_name, options[choice])
                st.session_state["flash"] = "Entry deleted."
                st.rerun()
            except Exception as e:
                st.error("Could not delete: " + str(e))
