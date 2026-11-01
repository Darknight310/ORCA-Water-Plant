import base64
import datetime as dt
import hmac
import json
import time

import streamlit as st
import streamlit.components.v1 as components

import db
import ui

st.set_page_config(page_title="ORCA Water", layout="wide", initial_sidebar_state="collapsed")
ui.inject_css()


def _supabase_key():
    try:
        return st.secrets.get("SUPABASE_SERVICE_KEY") or st.secrets.get("SUPABASE_KEY")
    except Exception:
        return None


def secrets_ok():
    try:
        return bool(st.secrets.get("SUPABASE_URL") and _supabase_key() and st.secrets.get("APP_PASSWORD"))
    except Exception:
        return False


def _key_is_public(key):
    """True if the configured key is a public (anon / publishable) key. This app runs
    entirely on the server behind the app password, and the database is deliberately
    locked so public keys can access nothing - so a public key here means the wrong
    key was pasted into the secrets."""
    if not key:
        return False
    k = str(key).strip()
    if k.startswith("sb_publishable_"):
        return True
    if k.startswith("sb_secret_"):
        return False
    parts = k.split(".")
    if len(parts) == 3:  # legacy JWT key: read (not verify) the role claim
        try:
            payload = parts[1] + "=" * (-len(parts[1]) % 4)
            role = json.loads(base64.urlsafe_b64decode(payload)).get("role")
            return role in ("anon", "authenticated")
        except Exception:
            return False
    return False


if not secrets_ok():
    st.error("The app's secrets are not set yet.")
    st.markdown("In Streamlit: **Manage App \u2192 Settings \u2192 Secrets**, then add "
                "`SUPABASE_URL`, `SUPABASE_SERVICE_KEY` (the service_role / secret key - "
                "the older name `SUPABASE_KEY` also works) and `APP_PASSWORD`.")
    st.stop()

if _key_is_public(_supabase_key()):
    st.error("Wrong Supabase key: a public (anon / publishable) key is set in the app secrets.")
    st.markdown("This database is locked so public keys can access **nothing**. In Streamlit "
                "**Settings \u2192 Secrets**, set `SUPABASE_SERVICE_KEY` to the **service_role / secret** "
                "key from Supabase (Project Settings \u2192 API). Keep that key only in these "
                "server-side secrets - never put it in code or share it.")
    st.stop()

@st.cache_resource
def _guard():
    return {"fails": [], "locked_until": 0.0}


def _stop_password_suggestion():
    """Tells the browser this password box is for SIGNING IN to an existing
    account, not creating a new one, so Chrome/Edge stop offering to
    generate and save a brand new password here."""
    components.html("""
    <script>
    (function() {
      function patch() {
        try {
          var doc = window.parent.document;
          var fields = doc.querySelectorAll('input[type="password"]');
          fields.forEach(function(el) {
            el.setAttribute('autocomplete', 'current-password');
          });
        } catch (e) {}
      }
      patch();
      var obs = new MutationObserver(patch);
      try {
        obs.observe(window.parent.document.body, {childList: true, subtree: true});
      } catch (e) {}
      setTimeout(function() { obs.disconnect(); }, 8000);
    })();
    </script>
    """, height=0, width=0)


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
            _stop_password_suggestion()
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
