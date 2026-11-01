# 2026-11-01 cleanup & unification (applied to live database)

Record of one-time data changes made on 2026-11-01. Read this before touching the
history tables. A safety copy of the affected tables as they were just before the
change is kept in the database schema `orca_backup_20261101` (production,
invoice_lines, sale_batch_usage, production_batch_usage, sale_order_lines).

## What was cleaned
- Invoices INV#100 / INV#101 had been deleted by the owner; sale orders SO#7/SO#8
  returned to Pending automatically.
- All four invented `Auto (Stock Shortfall)` production batches (ids 11-14, which
  had no sales attached after the deletions) were deleted. After this, the maths
  stock register and the batch stock register agree exactly (0 mismatches).
- SO#7's second line was corrected from "500 ml Mix PET" to "500 ml Pure PET"
  (it is a Pending order, so this is reversible in one click; rate PKR 320 was the
  Pure rate - Mix historically sold at PKR 220 - and only Pure products were
  produced for these orders).

## How history was unified (Fix 2 data backfill)
- The four `OPENING-HISTORY` production rows (ids 5-8) received production_batch_usage
  rows (recipe x bundles against the single opening batch per material) and their
  `total_cost` was set from that usage (143.30 / 208.61 / 171.90 / 235.24 per bundle).
- The 153 pre-FIFO invoice lines with `cogs_amount = 0` were backfilled at those
  opening costs (total PKR 136,029.34) and given matching sale_batch_usage rows
  against the opening production of their product. Total COGS after backfill:
  PKR 143,206.40 - exactly the same as the old dashboard figure, so no reported
  profit changed; the cost is now stored per invoice line instead of recomputed.
- Views v_raw_stock, v_product_stock, v_pnl were replaced (see schema.sql):
  stock balances/values now come from batches in hand; P&L COGS is
  SUM(invoice_lines.cogs_amount). v_product_cost.std_cost remains only as a
  "today's estimated cost" display.
- App code no longer invents shortage batches: production, damages and invoices
  are blocked with a clear message when recorded stock is not enough.

## Resulting state after cleanup (before re-adding SO#7/SO#8 invoices)
- Finished stock: 1500 ml Pure = 3 bundles, 500 ml Pure = 2 bundles, others 0.
- Pending SO#7 + SO#8 need 7 x 1500 Pure and 6 x 500 Pure, i.e. 4 more bundles of
  each must be produced/recorded before those orders can be invoiced.
- Receivables PKR 20,790; Net sales PKR 196,470; COGS PKR 143,206.40;
  Current (retained) profit PKR 21,153.60.
