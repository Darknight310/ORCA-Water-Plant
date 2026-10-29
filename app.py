import datetime as dt
import hmac
import time

import streamlit as st

import db
import ui

st.set_page_config(page_title="ORCA Water", layout="wide", initial_sidebar_state="collapsed")
ui.inject_css()


def secrets_ok():
    try:
        return all(k in st.secrets for k in ("SUPABASE_URL", "SUPABASE_KEY", "APP_PASSWORD"))
    except Exception:
        return False


if not secrets_ok():
    st.error("The app's secrets are not set yet.")
    st.markdown("In Streamlit: **Manage App → Settings → Secrets**, then add "
                "`SUPABASE_URL`, `SUPABASE_KEY` and `APP_PASSWORD`.")
    st.stop()

@st.cache_resource
def _guard():
    return {"fails": [], "locked_until": 0.0}


if not st.session_state.get("auth"):
    _, mid, _ = st.columns([1, 1.1, 1])
    with mid:
        st.markdown("<div style='height:12vh'></div>"
                    "<div class='pg-title'>ORCA Water</div>"
                    "<div class='pg-sub'>Plant Management · Sign In To Continue</div>",
                    unsafe_allow_html=True)
        guard = _guard()
        now = time.time()
        if now < guard["locked_until"]:
            st.error("Too many wrong attempts. Try again in " + str(int((guard["locked_until"] - now) // 60) + 1) + " minute(s).")
        else:
            with st.form("login"):
                pw = st.text_input("Password", type="password")
                go = st.form_submit_button("Sign In", type="primary")
            if go:
                if hmac.compare_digest(pw.encode(), str(st.secrets["APP_PASSWORD"]).encode()):
                    guard["fails"] = []
                    st.session_state["auth"] = True
                    st.rerun()
                else:
                    time.sleep(1)
                    guard["fails"] = [t for t in guard["fails"] if now - t < 600] + [now]
                    if len(guard["fails"]) >= 5:
                        guard["locked_until"] = now + 600
                        guard["fails"] = []
                    st.error("Wrong password.")
    st.stop()

pages = [
    st.Page("views/dashboard.py", title="Dashboard", icon=":material/space_dashboard:", default=True),
    st.Page("views/customers.py", title="Customers", icon=":material/groups:"),
    st.Page("views/sales.py", title="Sales & Invoices", icon=":material/receipt_long:"),
    st.Page("views/stock.py", title="Stock & Production", icon=":material/inventory_2:"),
    st.Page("views/suppliers_purchases.py", title="Suppliers & Purchases", icon=":material/local_shipping:"),
    st.Page("views/expenses.py", title="Expenses & Draws", icon=":material/payments:"),
    st.Page("views/reports.py", title="Reports", icon=":material/bar_chart:"),
]
try:
    nav = st.navigation(pages, position="top")
except TypeError:
    nav = st.navigation(pages)

with st.sidebar:
    st.caption("Backup")
    if st.button("Prepare Excel Backup"):
        try:
            st.session_state["backup"] = db.export_all()
        except Exception as e:
            st.error("Backup failed: " + str(e))
    if "backup" in st.session_state:
        st.download_button("Download Backup", st.session_state["backup"],
                           file_name="ORCA_backup_" + dt.date.today().isoformat() + ".xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if st.button("Sign Out"):
        st.session_state.clear()
        st.rerun()

nav.run()
