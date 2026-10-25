import datetime as dt
import hmac
import time

import streamlit as st

import db
import ui

st.set_page_config(page_title="ORCA Water", page_icon="💧", layout="wide",
                   initial_sidebar_state="expanded")
ui.inject_css()


def secrets_ok():
    try:
        return all(k in st.secrets for k in ("SUPABASE_URL", "SUPABASE_KEY", "APP_PASSWORD"))
    except Exception:
        return False


if not secrets_ok():
    st.error("The app's secrets are not set yet.")
    st.markdown("In Streamlit: **Manage app → Settings → Secrets**, then add "
                "`SUPABASE_URL`, `SUPABASE_KEY` and `APP_PASSWORD`.")
    st.stop()

if not st.session_state.get("auth"):
    _, mid, _ = st.columns([1, 1.1, 1])
    with mid:
        st.markdown("<div style='height:12vh'></div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:2.6rem'>💧</div>"
                    "<div class='pg-title'>ORCA Water</div>"
                    "<div class='pg-sub'>Plant management · sign in to continue</div>",
                    unsafe_allow_html=True)
        with st.form("login"):
            pw = st.text_input("Password", type="password")
            go = st.form_submit_button("Sign in", type="primary")
        if go:
            if hmac.compare_digest(pw.encode(), str(st.secrets["APP_PASSWORD"]).encode()):
                st.session_state["auth"] = True
                st.rerun()
            else:
                time.sleep(1)
                st.error("Wrong password.")
    st.stop()

pages = [
    st.Page("views/dashboard.py", title="Dashboard", icon=":material/space_dashboard:", default=True),
    st.Page("views/sales.py", title="Sales & Invoices", icon=":material/receipt_long:"),
    st.Page("views/customers.py", title="Customers", icon=":material/groups:"),
    st.Page("views/stock.py", title="Stock & Production", icon=":material/inventory_2:"),
    st.Page("views/expenses.py", title="Expenses & Draws", icon=":material/payments:"),
]
nav = st.navigation(pages)

with st.sidebar:
    st.divider()
    st.caption("Backup")
    if st.button("Prepare Excel backup"):
        try:
            st.session_state["backup"] = db.export_all()
        except Exception as e:
            st.error("Backup failed: " + str(e))
    if "backup" in st.session_state:
        st.download_button("Download backup", st.session_state["backup"],
                           file_name="ORCA_backup_" + dt.date.today().isoformat() + ".xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if st.button("Sign out"):
        st.session_state.clear()
        st.rerun()

nav.run()
