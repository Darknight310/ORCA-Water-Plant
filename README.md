# ORCA Water Plant

A Streamlit app for running a small bottled-water plant: customers, sale orders,
invoices & payments, raw-material batches (FIFO), production, finished-goods stock,
suppliers & purchases, expenses/owner draws, damages, reports and a live
Profit & Loss / Cash-in-Hand dashboard. Data lives in Supabase (Postgres).

## How it fits together
- `app.py` - login (single shared app password) and page navigation.
- `views/` - the screens (Dashboard, Customers, Sales, Stock, Suppliers, Expenses, Reports).
- `db.py` - all database access and the stock/cost rules.
- `supabase/schema.sql` - the **complete database blueprint** (tables, constraints,
  views, indexes, security). Run it once in a fresh Supabase project to rebuild the DB.
- `supabase/verify.sql` - read-only health checks (all "problems" should be 0).

## The costing & stock rules (please read before changing db.py / views)
1. **Batches are the single truth for stock.** Raw stock in hand = sum of
   `raw_material_batches.qty_remaining`; finished stock = sum of `production.qty_remaining`.
   The `v_raw_stock` / `v_product_stock` views read exactly those.
2. **Costs are locked at the moment things happen.** Production consumes the oldest
   raw batches first (FIFO) and stores its real `total_cost`; a sale consumes the
   oldest production batches first and stores the line's real `invoice_lines.cogs_amount`.
   The dashboard P&L (`v_pnl`) simply sums those locked costs - profit is never
   recomputed from today's prices, and per-invoice profit always matches the dashboard.
   `v_product_cost.std_cost` ("Cost / Bundle") is only a *today's estimate* display.
3. **Stock is never invented.** If recorded stock cannot cover a production run,
   damage, or invoice, saving is blocked with a clear message. Record the missing
   purchase/production first. (Older versions silently created "Auto (Stock Shortfall)"
   batches - removed 2026-11-01; see `supabase/2026-11-01_cleanup_and_unify_NOTES.md`.)
4. **Physical Count adjusts the batches** (visible "Physical Count Adjustment"
   batches), so all stock screens keep agreeing with your real count.
5. **Saved lines are correctable from their own screens.** Use **Edit Full Line**
   on a selected row. Dates and ordinary details simply update. Stock-affecting
   corrections keep the ledgers together: a damage puts its old quantity back
   into the exact batch(es) recorded in `damage_batch_usage`, then takes the
   corrected quantity FIFO again; a purchase and its batch are corrected
   together; an unused production run returns its raw materials and is rebuilt.
   Totals and locked costs are results, so they recalculate from the corrected
   source details instead of being typed over. If a later sale/damage/count
   already used the stock, the app explains which dependent entry must be
   corrected first rather than silently desyncing stock or profit.

## Secrets (Streamlit: Manage App -> Settings -> Secrets)
```toml
SUPABASE_URL = "https://<your-project-ref>.supabase.co"
SUPABASE_SERVICE_KEY = "<service_role / secret key>"
APP_PASSWORD = "<app login password>"
```
The older name `SUPABASE_KEY` is also accepted. Use the **service_role/secret** key,
kept only in these server-side secrets. The database deliberately gives public
(anon/publishable) keys **no access at all** (RLS on, no policies, no grants), and
the app refuses to start with a public key so a wrong paste fails loudly.

## Run locally
```bash
pip install -r requirements.txt
# create .streamlit/secrets.toml with the three secrets above (never commit it)
streamlit run app.py
```

## After merging an update on Streamlit Cloud
`app.py` checks whether `db.py` / `ui.py` changed and reloads them, because a
long-running Streamlit process can otherwise keep using an older copy of those
helper files after the page files have updated. If an error appears immediately
after a merge, wait a minute and refresh; if it stays, use **Manage app ->
Reboot app**. Rebooting does not affect the data in Supabase.

## Backups
- **Data:** Sidebar -> "Prepare Excel Backup" exports every table to one .xlsx.
  Do this regularly and keep the file somewhere safe.
- **Structure:** `supabase/schema.sql` in this repo rebuilds the empty database.
