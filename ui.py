import math

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
header[data-testid="stHeader"] { background: rgba(247,249,251,.88); backdrop-filter: blur(10px); }
.block-container { padding-top: 5rem; padding-bottom: 3rem; max-width: 1280px; }

/* smooth transitions between pages and sections */
@keyframes ofade { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
[data-testid="stMainBlockContainer"] { animation: ofade .35s ease-out; }
[data-testid="stElementContainer"] { animation: ofade .3s ease-out; }

.pg-title { font-size: 1.9rem; font-weight: 800; letter-spacing: -0.03em; line-height: 1.1; }
.pg-sub { opacity: .6; margin: .3rem 0 1.4rem 0; font-size: .95rem; }
h4 { font-weight: 700; letter-spacing: -0.01em; }

/* soft rounded surfaces */
.card, [data-testid="stMetric"], [data-testid="stExpander"], .tile {
  background: #FFFFFF; border: 1px solid rgba(15,23,42,.07); border-radius: 20px;
  box-shadow: 0 1px 2px rgba(15,23,42,.04), 0 10px 28px rgba(15,23,42,.05); }
.card { padding: 20px 22px; }
[data-testid="stMetric"] { padding: 18px 20px; min-height: 112px; }
[data-testid="stMetricLabel"] p { font-size: .74rem; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; opacity: .65; }
[data-testid="stMetricValue"] { font-weight: 800; letter-spacing: -0.02em; }
[data-testid="stExpander"] { overflow: hidden; }
[data-testid="stDataFrame"] { border-radius: 16px; overflow: hidden; border: 1px solid rgba(15,23,42,.08); }
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button { border-radius: 12px; font-weight: 600; padding: .5rem 1.15rem; }
[data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="textarea"] { border-radius: 12px !important; }
[data-testid="stSidebar"] { border-right: 1px solid rgba(15,23,42,.08); }

/* dashboard tiles (whole tile is a link to its page) */
[class*="st-key-tile_"] { position: relative; gap: 0 !important; }
[class*="st-key-tile_"] [data-testid="stElementContainer"],
[class*="st-key-tile_"] [data-testid="stPageLink"] { position: static !important; height: 0; margin: 0; padding: 0; overflow: visible; }
[class*="st-key-tile_"] a { position: absolute; inset: 0; opacity: 0; z-index: 5; border-radius: 20px; }
.tile { padding: 18px 20px; min-height: 124px; transition: transform .2s ease, box-shadow .2s ease; }
[class*="st-key-tile_"]:hover .tile { transform: translateY(-3px); box-shadow: 0 2px 4px rgba(15,23,42,.05), 0 16px 34px rgba(14,116,144,.14); }
.tl { font-size: .74rem; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; opacity: .62; }
.tv { font-size: 1.65rem; font-weight: 800; letter-spacing: -0.02em; margin-top: .35rem; line-height: 1.15; }
.ts { font-size: .82rem; opacity: .6; margin-top: .45rem; }

/* profit & loss table */
.pnl { width: 100%; border-collapse: separate; border-spacing: 0 4px; font-size: .95rem; }
.pnl th { text-align: left; font-size: .72rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; opacity: .5; padding: .3rem 1rem .7rem; }
.pnl th.r, .pnl td.r { text-align: right; }
.pnl td { padding: .95rem 1rem; font-weight: 600; }
.pnl td.r { font-variant-numeric: tabular-nums; white-space: nowrap; }
.pnl tr.hl td { background: rgba(15,23,42,.04); font-weight: 700; }
.pnl tr.hl td:first-child { border-radius: 14px 0 0 14px; }
.pnl tr.hl td:last-child { border-radius: 0 14px 14px 0; }
.pnl tr.hl.t-green td { background: rgba(4,120,87,.08); }
.pnl tr.hl.t-blue td { background: rgba(29,78,216,.08); }
.pnl tr.hl.t-cyan td { background: rgba(14,116,144,.08); }
.t-ink { color: #0F172A; } .t-amber { color: #B45309; } .t-green { color: #047857; } .t-rose { color: #BE123C; }
.t-cyan { color: #0E7490; } .t-purple { color: #7E22CE; } .t-blue { color: #1D4ED8; }
.pnl td.pc { opacity: .75; width: 90px; }
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def header(title, subtitle=""):
    st.markdown('<div class="pg-title">' + title + '</div><div class="pg-sub">' + subtitle + '</div>',
                unsafe_allow_html=True)
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


# ------------------------------------------------------------------ navigation
def sections(options, key, default=None):
    """Tab-like switcher that remembers its choice, and can be switched from code."""
    gk = "goto_" + key
    if gk in st.session_state:
        target = st.session_state.pop(gk)
        if target in options:
            st.session_state[key] = target
    if st.session_state.get(key) not in options:
        st.session_state[key] = default or options[0]
    try:
        sel = st.segmented_control("Section", options, key=key, label_visibility="collapsed")
    except AttributeError:
        sel = st.radio("Section", options, key=key, horizontal=True, label_visibility="collapsed")
    return sel if sel in options else (default or options[0])


def goto(key, option):
    st.session_state["goto_" + key] = option


# ---------------------------------------------------------------------- tiles
def tile(key, label, value, sub, target):
    with st.container(key="tile_" + key):
        st.markdown('<div class="tile"><div class="tl">' + label + '</div><div class="tv">' + value +
                    '</div><div class="ts">' + sub + '</div></div>', unsafe_allow_html=True)
        st.page_link(target, label="Open")


def pnl_table(rows):
    """rows: (label, amount, percent, tone, highlighted)"""
    html = ("<table class='pnl'><tr><th>Financial Category</th><th class='r'>Amount (PKR)</th>"
            "<th class='r'>% Of Net Sales</th></tr>")
    for label, amount, pct, tone, hl in rows:
        shown = money(amount, 2) if amount >= 0 else "-" + money(-amount, 2)
        cls = ("hl " if hl else "") + "t-" + tone
        html += ("<tr class='" + cls + "'><td class='t-" + tone + "'>" + label + "</td><td class='r t-" + tone + "'>" +
                 shown + "</td><td class='r pc t-" + tone + "'>" + f"{pct:.1f}%" + "</td></tr>")
    html += "</table>"
    st.markdown("<div class='card'>" + html + "</div>", unsafe_allow_html=True)


# --------------------------------------------------------------------- charts
def chart(fig):
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(t=10, b=10, l=10, r=10), height=320,
                      legend=dict(orientation="h", y=-0.1))
    try:
        st.plotly_chart(fig, width="stretch")
    except Exception:
        st.plotly_chart(fig, use_container_width=True)


def altair(ch):
    try:
        st.altair_chart(ch, width="stretch")
    except Exception:
        st.altair_chart(ch, use_container_width=True)


# --------------------------------------------------------------------- tables
def _height(n):
    return 35 * (n + 1) + 3


def table(df, **kw):
    """Plain table that grows to show every row (no scrolling inside the table)."""
    h = _height(min(len(df), 60))
    try:
        st.dataframe(df, width="stretch", hide_index=True, height=h, **kw)
    except Exception:
        st.dataframe(df, use_container_width=True, hide_index=True, height=h, **kw)


def _grid(disp, key):
    h = _height(len(disp))
    kw = dict(hide_index=True, key=key, on_select="rerun", selection_mode="single-row", height=h)
    try:
        return st.dataframe(disp, width="stretch", **kw)
    except Exception:
        try:
            return st.dataframe(disp, use_container_width=True, **kw)
        except Exception:
            st.dataframe(disp, hide_index=True, height=h)
            return None


def _isnull(v):
    return v is None or (isinstance(v, float) and pd.isna(v))


def _cell(rec, getter, dec):
    v = getter(rec) if callable(getter) else rec.get(getter)
    if _isnull(v):
        return ""
    if dec is None:
        return str(v)
    try:
        return f"{float(v):,.{dec}f}"
    except (TypeError, ValueError):
        return str(v)


def _edit_form(key, table_name, rec, fields, validate):
    st.markdown("**Edit Entry**")
    values = {}
    cols = st.columns(2)
    for i, f in enumerate(fields):
        c = cols[i % 2]
        col = f["col"]
        wk = "ef_%s_%s_%s" % (key, rec["id"], col)
        cur = rec.get(col)
        kind = f.get("kind", "text")
        if kind == "text":
            values[col] = c.text_input(f["label"], value="" if _isnull(cur) else str(cur), key=wk)
        elif kind == "num":
            values[col] = c.number_input(f["label"], min_value=0.0, value=0.0 if _isnull(cur) else float(cur),
                                         step=f.get("step", 1.0), key=wk)
        elif kind == "date":
            values[col] = c.date_input(f["label"], value=pd.to_datetime(cur).date(), key=wk)
        elif kind == "choice":
            opts = list(f["options"])
            values[col] = c.selectbox(f["label"], opts, index=opts.index(cur) if cur in opts else None, key=wk)
        elif kind == "select":
            ids = list(f["options"].keys())
            names = list(f["options"].values())
            idx = ids.index(cur) if cur in ids else None
            pick = c.selectbox(f["label"], names, index=idx, key=wk)
            values[col] = ids[names.index(pick)] if pick is not None else None
    b1, b2 = st.columns(2)
    if b1.button("Save Changes", type="primary", key="es_%s_%s" % (key, rec["id"])):
        payload = {}
        problem = None
        for f in fields:
            col, v, kind = f["col"], values[f["col"]], f.get("kind", "text")
            if kind == "text":
                v = (v or "").strip() or None
            elif kind == "num":
                v = float(v)
            elif kind == "date":
                v = v.isoformat()
            if f.get("required") and (v is None or v == ""):
                problem = f["label"] + " is required."
            payload[col] = v
        if not problem and validate:
            problem = validate(payload, rec)
        if problem:
            st.error(problem)
        else:
            try:
                db.update(table_name, rec["id"], payload)
                st.session_state["tv_" + key] = st.session_state.get("tv_" + key, 0) + 1
                st.session_state.pop("edit_" + key, None)
                st.session_state["flash"] = "Changes saved."
                st.rerun()
            except Exception as e:
                st.error("Could not save: " + str(e))
    if b2.button("Cancel", key="ec_%s_%s" % (key, rec["id"])):
        st.session_state.pop("edit_" + key, None)
        st.rerun()


def entity_table(key, df, columns, table=None, fields=None, label=None, on_edit=None, on_delete=None,
                 extras=None, detail=None, size=25, validate=None, can_edit=None, can_delete=None):
    """A table you click a row in. Action buttons appear ABOVE the table for the selected row.

    columns: list of (header, column name or function(record), decimals or None)
    fields : edit-form spec for the generic Edit button (needs `table`)
    extras : list of (button label, function(record)[, show_if(record)])
    detail : (button label, function(record)) shows extra content above the table
    """
    if df is None or df.empty:
        st.info("Nothing here yet.")
        return
    label = label or (lambda r: "#" + str(r["id"]))
    df = df.reset_index(drop=True)
    total = len(df)
    pages = max(1, math.ceil(total / size))
    pk = "pg_" + key
    page = min(max(int(st.session_state.get(pk, 1)), 1), pages)
    part = df.iloc[(page - 1) * size: page * size].reset_index(drop=True)
    recs = part.to_dict("records")
    disp = pd.DataFrame({hdr: [_cell(r, g, d) for r in recs] for hdr, g, d in columns})
    ver = st.session_state.get("tv_" + key, 0)

    bar = st.container()
    ev = _grid(disp, "tbl_%s_%d_%d" % (key, ver, page))
    try:
        sel = list(ev.selection.rows)
    except Exception:
        sel = []

    if pages > 1:
        p1, p2, p3 = st.columns([1, 1, 4])
        if p1.button("Previous", key="pv_" + key, disabled=page <= 1):
            st.session_state[pk] = page - 1
            st.rerun()
        if p2.button("Next", key="nx_" + key, disabled=page >= pages):
            st.session_state[pk] = page + 1
            st.rerun()
        p3.caption("Page %d Of %d  ·  %d Rows" % (page, pages, total))

    with bar:
        if not sel or sel[0] >= len(recs):
            if table or on_edit or on_delete or extras or detail:
                st.caption("Click A Row In The Table To Edit, Delete Or Use More Actions.")
            return
        rec = recs[sel[0]]
        ek, dk, vk = "edit_" + key, "del_" + key, "view_" + key
        st.markdown("**Selected:** " + label(rec))
        buttons = []
        if (fields or on_edit) and (can_edit is None or can_edit(rec)):
            buttons.append("edit")
        if detail:
            buttons.append("detail")
        for x in (extras or []):
            if len(x) < 3 or x[2](rec):
                buttons.append(x)
        if can_delete is None or can_delete(rec):
            buttons.append("delete")
        cols = st.columns(max(len(buttons), 1) + 1)
        for i, b in enumerate(buttons):
            c = cols[i]
            if b == "edit":
                if c.button("Edit", key=key + "_edit"):
                    if on_edit:
                        on_edit(rec)
                    else:
                        st.session_state[ek] = rec["id"]
                        st.session_state.pop(dk, None)
            elif b == "detail":
                if c.button(detail[0], key=key + "_detail"):
                    st.session_state[vk] = None if st.session_state.get(vk) == rec["id"] else rec["id"]
            elif b == "delete":
                if c.button("Delete", key=key + "_delete"):
                    st.session_state[dk] = rec["id"]
                    st.session_state.pop(ek, None)
            else:
                if c.button(b[0], key=key + "_x_" + b[0]):
                    b[1](rec)
        if st.session_state.get(vk) == rec["id"] and detail:
            detail[1](rec)
        if st.session_state.get(ek) == rec["id"] and fields:
            _edit_form(key, table, rec, fields, validate)
        if st.session_state.get(dk) == rec["id"]:
            st.warning("Delete " + label(rec) + "? This cannot be undone.")
            d1, d2, _ = st.columns([1, 1, 3])
            if d1.button("Yes, Delete", type="primary", key=key + "_yes"):
                try:
                    if on_delete:
                        on_delete(rec)
                    else:
                        db.delete(table, rec["id"])
                    st.session_state["tv_" + key] = ver + 1
                    st.session_state.pop(dk, None)
                    st.session_state["flash"] = "Entry deleted."
                    st.rerun()
                except Exception as e:
                    msg = str(e)
                    if "foreign key" in msg.lower() or "violates" in msg.lower():
                        st.error("This entry is used by other records, so it cannot be deleted.")
                    else:
                        st.error("Could not delete: " + msg)
            if d2.button("Cancel", key=key + "_no"):
                st.session_state.pop(dk, None)
                st.rerun()
