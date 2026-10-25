import pandas as pd
import streamlit as st

import db
import ui

ui.header("Customers", "Your clients and what each one owes")

customers = db.get("customers", order="name")
summ = db.get("v_invoice_summary", order="id")

if customers.empty:
    st.info("No customers yet.")
else:
    if summ.empty:
        agg = pd.DataFrame(columns=["customer_id", "billed", "owed"])
    else:
        s = summ.assign(owed=summ["balance_due"].clip(lower=0))
        agg = s.groupby("customer_id").agg(billed=("net_amount", "sum"), owed=("owed", "sum")).reset_index()
    df = customers.merge(agg, left_on="id", right_on="customer_id", how="left")
    df["billed"] = df["billed"].fillna(0)
    df["owed"] = df["owed"].fillna(0)

    k1, k2, k3 = st.columns(3)
    k1.metric("Customers", str(len(df)))
    k2.metric("With a balance due", str(int((df["owed"] > 0).sum())))
    k3.metric("Total owed to you", "PKR " + ui.money(df["owed"].sum()))

    q = st.text_input("Search", placeholder="Name, area or phone", key="cust_search")
    v = df
    if q:
        mask = pd.Series(False, index=df.index)
        for c in ["name", "address", "phone", "contact_person"]:
            mask = mask | df[c].fillna("").str.contains(q, case=False)
        v = df[mask]
    v = v.sort_values(["owed", "name"], ascending=[False, True])
    show = v[["name", "category", "contact_person", "phone", "address", "billed", "owed"]]
    show = ui.fmt(show, ["billed", "owed"])
    show.columns = ["Customer", "Category", "Contact", "Phone", "Address", "Total billed", "Balance due"]
    ui.table(show)

with st.expander("Add a new customer"):
    n = st.session_state.setdefault("cust_n", 0)
    a, b = st.columns(2)
    name = a.text_input("Customer / shop name", key="c_name_" + str(n))
    category = b.text_input("Category (optional)", key="c_cat_" + str(n))
    c, d = st.columns(2)
    person = c.text_input("Contact person", key="c_per_" + str(n))
    phone = d.text_input("Phone", key="c_ph_" + str(n))
    address = st.text_input("Address / area", key="c_adr_" + str(n))
    if st.button("Add customer", type="primary", key="c_save_" + str(n)):
        nm = name.strip()
        if not nm:
            st.error("Enter the customer name.")
        elif not customers.empty and nm.lower() in customers["name"].str.lower().tolist():
            st.error("A customer with this name already exists.")
        else:
            try:
                db.insert("customers", {"name": nm, "category": category.strip() or None,
                                        "contact_person": person.strip() or None,
                                        "phone": phone.strip() or None, "address": address.strip() or None})
                st.session_state["cust_n"] = n + 1
                st.session_state["flash"] = "Customer " + nm + " added."
                st.rerun()
            except Exception as e:
                st.error("Could not add the customer: " + str(e))
