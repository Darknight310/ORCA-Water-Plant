import math

import pandas as pd
import streamlit as st

import db

ACCENT = "#38BDF8"
PALETTE = ["#38BDF8", "#FBBF24", "#F87171", "#C084FC", "#34D399"]
GRID = "rgba(148,163,184,.18)"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
.stApp, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p, .stApp label,
.stApp input, .stApp textarea, .stApp button { font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 5rem; padding-bottom: 3rem; max-width: 1280px; }

/* smooth transitions between pages and sections */
@keyframes ofade { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
[data-testid="stMainBlockContainer"] { animation: ofade .35s ease-out; }
[data-testid="stElementContainer"] { animation: ofade .3s ease-out; }

.pg-title { font-size: 1.9rem; font-weight: 800; letter-spacing: -0.03em; line-height: 1.1; }
.pg-sub { opacity: .6; margin: .3rem 0 1.4rem 0; font-size: .95rem; }
h4 { font-weight: 700; letter-spacing: -0.01em; }

/* dark cards: each one sets its own background AND text colour, so it is readable on any theme */
.card, .tile, [data-testid="stMetric"] {
  background: #111827; color: #F8FAFC; border: 1px solid #1F2937; border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0,0,0,.22); }
.card { padding: 20px 22px; }
[data-testid="stMetric"] { padding: 18px 20px; min-height: 112px; }
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p { color: #94A3B8 !important; font-size: .74rem; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; }
[data-testid="stMetricValue"], [data-testid="stMetricValue"] div { color: #FFFFFF !important; font-weight: 800; letter-spacing: -0.02em; }
[data-testid="stMetricDelta"], [data-testid="stMetricDelta"] div { color: #94A3B8 !important; }
[data-testid="stExpander"] { border-radius: 16px; overflow: hidden; }
[data-testid="stDataFrame"] { border-radius: 16px; overflow: hidden; border: 1px solid rgba(148,163,184,.25); }
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button { border-radius: 12px; font-weight: 600; padding: .5rem 1.15rem; }
[data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="textarea"] { border-radius: 12px !important; }

/* dashboard tiles (the whole tile is a link to its page) */
[class*="st-key-tile_"] { position: relative; gap: 0 !important; }
[class*="st-key-tile_"] [data-testid="stElementContainer"] { animation: none; }
[class*="st-key-tile_"] > [data-testid="stElementContainer"]:last-child { position: static !important; height: 0; margin: 0 !important; padding: 0 !important; overflow: visible; }
[class*="st-key-tile_"] [data-testid="stPageLink"] { position: static !important; height: 0; overflow: visible; }
[class*="st-key-tile_"] a { position: absolute; inset: 0; opacity: 0; z-index: 5; border-radius: 20px; }
.tile { padding: 18px 20px; min-height: 124px; transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease; }
[class*="st-key-tile_"]:hover .tile { transform: translateY(-3px); border-color: #38BDF8; box-shadow: 0 16px 34px rgba(56,189,248,.16); }
.tl { color: #94A3B8; font-size: .74rem; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; }
.tv { color: #FFFFFF; font-size: 1.65rem; font-weight: 800; letter-spacing: -0.02em; margin-top: .35rem; line-height: 1.15;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ts { color: #94A3B8; font-size: .82rem; margin-top: .45rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* profit & loss card */
.pnl-card { padding: 22px 24px 8px; }
.pnl-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.pnl-title { font-size: 1.05rem; font-weight: 800; color: #F8FAFC; letter-spacing: -0.01em; }
.pnl-badge { background: rgba(56,189,248,.14); color: #7DD3FC; font-size: .68rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: .05em; padding: .32rem .75rem; border-radius: 999px; white-space: nowrap; }
.pnl-cols, .pnl-row { display: grid; grid-template-columns: 1fr 150px 86px; align-items: center; column-gap: .6rem; }
.pnl-cols { padding: 0 .5rem .6rem; }
.pnl-cols span { color: #64748B; font-size: .67rem; font-weight: 700; text-transform: uppercase; letter-spacing: .07em; }
.pnl-cols .pnl-amt, .pnl-cols .pnl-pct { text-align: right; }
.pnl-row { padding: .9rem .5rem; border-bottom: 1px solid rgba(148,163,184,.09); font-weight: 600; font-size: .93rem; border-radius: 10px; }
.pnl-rows .pnl-row:last-child { border-bottom: none; }
.pnl-row.hl { background: rgba(22,32,50,.75); font-weight: 700; margin: 3px 0; }
.pnl-row.hl.hb { background: rgba(30,38,64,.6); }
.pnl-row .pnl-amt, .pnl-row .pnl-pct { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.t-ink { color: #FFFFFF; } .t-muted { color: #94A3B8; } .t-amber { color: #FBBF24; } .t-green { color: #34D399; }
.t-rose { color: #F87171; } .t-cyan { color: #38BDF8; } .t-purple { color: #C084FC; } .t-blue { color: #60A5FA; }

/* donut chart legend */
.dchip-row { display: flex; align-items: center; justify-content: space-between; padding: .6rem .3rem;
  border-bottom: 1px solid rgba(148,163,184,.09); font-size: .86rem; }
.dchip-row:last-child { border-bottom: none; }
.dchip-left { display: flex; align-items: center; gap: .6rem; color: #E2E8F0; font-weight: 600; }
.dchip-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.dchip-val { color: #F8FAFC; font-weight: 700; font-variant-numeric: tabular-nums; }
.dchip-pct { color: #64748B; font-size: .76rem; margin-left: .45rem; }

/* sub-tab switcher used across pages (ui.sections()) — each option as its own
   separate rounded box with a gap between them, instead of one joined strip */
[data-testid="stSegmentedControl"] div[data-baseweb="button-group"],
[data-testid="stSegmentedControl"] [role="radiogroup"] {
  gap: 10px !important; background: transparent !important; flex-wrap: wrap;
}
[data-testid="stSegmentedControl"] div[data-baseweb="button-group"] button,
[data-testid="stSegmentedControl"] [role="radiogroup"] button {
  border-radius: 12px !important; margin: 0 !important;
  background: #111827 !important; border: 1px solid #1F2937 !important;
  color: #CBD5E1 !important; font-weight: 600 !important;
}
[data-testid="stSegmentedControl"] button[aria-checked="true"],
[data-testid="stSegmentedControl"] button[data-testid="stBaseButton-primary"] {
  background: rgba(56,189,248,.14) !important; border-color: #38BDF8 !important; color: #7DD3FC !important;
}
div[role="radiogroup"][aria-label="Section"] { gap: 10px !important; flex-wrap: wrap; }
div[role="radiogroup"][aria-label="Section"] label {
  background: #111827 !important; border: 1px solid #1F2937 !important; border-radius: 12px !important;
  padding: .5rem 1rem !important; margin: 0 !important;
}

/* phone layout: switches automatically on screens up to 768px wide */
@media (max-width: 768px) {
  .block-container { padding: 5rem .8rem 2rem .8rem; }
  .pg-title { font-size: 1.5rem; }
  /* every tile is exactly the same height, so rows can never overlap */
  .tile { height: 128px; min-height: 0; padding: 12px 14px; overflow: hidden; }
  .tl { font-size: .64rem; line-height: 1.25; min-height: 2.5em; display: -webkit-box;
        -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  .tv { font-size: clamp(.95rem, 4.6vw, 1.25rem); margin-top: .25rem; }
  .ts { font-size: .72rem; margin-top: .3rem; }
  [class*="st-key-tile_"] { margin-bottom: .2rem; }
  [data-testid="stMetric"] { min-height: 92px; padding: 14px 16px; }
  [data-testid="stMetricValue"], [data-testid="stMetricValue"] div { font-size: 1.3rem; }
  .card { padding: 14px 12px; }
  .pnl-card { padding: 16px 14px 6px; }
  .pnl-title { font-size: .95rem; }
  .pnl-badge { font-size: .6rem; padding: .25rem .55rem; }
  .pnl-cols, .pnl-row { grid-template-columns: 1fr 108px 58px; column-gap: .3rem; }
  .pnl-row { padding: .7rem .3rem; font-size: .8rem; }
  .pnl-cols span { font-size: .6rem; }
  .dchip-row { font-size: .78rem; padding: .5rem .2rem; }
  .dchip-val { font-size: .8rem; }
  .dchip-pct { font-size: .68rem; }
  [data-testid="stSegmentedControl"] div[data-baseweb="button-group"] button,
  [data-testid="stSegmentedControl"] [role="radiogroup"] button,
  div[role="radiogroup"][aria-label="Section"] label { font-size: .8rem !important; padding: .4rem .7rem !important; }
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(4)),
  [data-testid="stHorizontalBlock"]:has(> [data-testid="column"]:nth-child(4)) { flex-wrap: wrap !important; gap: .7rem !important; }
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(4)) > [data-testid="stColumn"],
  [data-testid="stHorizontalBlock"]:has(> [data-testid="column"]:nth-child(4)) > [data-testid="column"] {
    flex: 1 1 calc(50% - .7rem) !important; min-width: calc(50% - .7rem) !important; }
}
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


def pnl_table(rows, title="Profit & Loss", badge="Live P&L"):
    """rows: (label, amount, percent, label colour, amount colour, percent colour, highlighted)

    Renders a borderless, card-style breakdown: a dark rounded card with a
    title + small pill badge up top, then plain-text Category / Amount /
    % Of Net Sales rows with subtle dividers and highlighted total bands.
    """
    body = ""
    for label, amount, pct, lt, at, pt, hl in rows:
        shown = money(amount, 2) if amount >= 0 else "-" + money(-amount, 2)
        cls = "pnl-row" + (" hl" + (" hb" if lt == "blue" else "") if hl else "")
        body += ("<div class='" + cls + "'><span class='t-" + lt + "'>" + label + "</span>"
                 "<span class='pnl-amt t-" + at + "'>" + shown + "</span>"
                 "<span class='pnl-pct t-" + pt + "'>" + f"{pct:.1f}%" + "</span></div>")
    html = ("<div class='card pnl-card'>"
            "<div class='pnl-head'><div class='pnl-title'>" + title + "</div>"
            "<div class='pnl-badge'>" + badge + "</div></div>"
            "<div class='pnl-cols'><span>Financial Category</span>"
            "<span class='pnl-amt'>Amount (PKR)</span>"
            "<span class='pnl-pct'>% Of Net Sales</span></div>"
            "<div class='pnl-rows'>" + body + "</div></div>")
    st.markdown(html, unsafe_allow_html=True)


# --------------------------------------------------------------------- charts
def chart(fig, height=320):
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(t=10, b=10, l=10, r=10), height=height,
                      legend=dict(orientation="h", y=-0.1))
    cfg = {"displayModeBar": False, "scrollZoom": False, "doubleClick": False}
    try:
        st.plotly_chart(fig, width="stretch", config=cfg)
    except Exception:
        st.plotly_chart(fig, use_container_width=True, config=cfg)


def donut(parts, center_label="", center_value=0, height=240):
    """A clean, borderless donut chart with the total in the middle and a
    custom card-style legend underneath (dot + label + amount + %)."""
    import plotly.graph_objects as go

    labels = list(parts.keys())
    values = list(parts.values())
    total = sum(values) or 1
    colors = (PALETTE * (len(labels) // len(PALETTE) + 1))[:len(labels)]

    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values, hole=0.72, sort=False,
        marker=dict(colors=colors, line=dict(width=0)),
        textinfo="none",
        hovertemplate="%{label}: PKR %{value:,.0f} (%{percent})<extra></extra>")])
    fig.update_layout(showlegend=False, annotations=[dict(
        text=(center_label + "<br>" if center_label else "") + "<b>" + money(center_value) + "</b>",
        x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#F8FAFC"))])
    chart(fig, height=height)

    rows = ""
    for lbl, val, col in zip(labels, values, colors):
        p = (val / total * 100) if total else 0
        rows += ("<div class='dchip-row'><div class='dchip-left'>"
                 "<span class='dchip-dot' style='background:" + col + ";'></span>" + lbl + "</div>"
                 "<div><span class='dchip-val'>PKR " + money(val) + "</span>"
                 "<span class='dchip-pct'>" + f"{p:.0f}%" + "</span></div></div>")
    st.markdown("<div class='card' style='padding:4px 16px;'>" + rows + "</div>", unsafe_allow_html=True)


def altair(ch):
    try:
        st.altair_chart(ch, width="stretch")
    except Exception:
        st.altair_chart(ch, use_container_width=True)


def bar_chart(df, x, y, horizontal=False, height=300):
    """Soft, rounded bars. Not interactive, so scrolling the page never moves the chart."""
    import altair as alt
    base = alt.Chart(df)
    if horizontal:
        ch = base.mark_bar(cornerRadiusEnd=10, size=22, color=ACCENT, opacity=0.92).encode(
            y=alt.Y(x + ":N", sort="-x", axis=alt.Axis(title=None, domain=False, ticks=False, labelLimit=240)),
            x=alt.X(y + ":Q", axis=alt.Axis(title=None, domain=False, ticks=False, gridColor=GRID, format="~s")),
            tooltip=[x, alt.Tooltip(y + ":Q", format=",.0f")])
    else:
        ch = base.mark_bar(cornerRadiusTopLeft=12, cornerRadiusTopRight=12, size=38, color=ACCENT, opacity=0.92).encode(
            x=alt.X(x + ":N", sort=None, axis=alt.Axis(title=None, labelAngle=0, domain=False, ticks=False)),
            y=alt.Y(y + ":Q", axis=alt.Axis(title=None, domain=False, ticks=False, gridColor=GRID, format="~s")),
            tooltip=[x, alt.Tooltip(y + ":Q", format=",.0f")])
    altair(ch.properties(height=height).configure_view(strokeWidth=0))


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
                 extras=None, detail=None, size=200, validate=None, can_edit=None, can_delete=None):
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
