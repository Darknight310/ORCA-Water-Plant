-- ============================================================
-- ORCA Water Plant - read-only health checks.
-- Run in Supabase SQL Editor any time. Every "problems" column should be 0.
-- ============================================================
-- 1) Stock: dashboard registers vs actual batches
SELECT
  (SELECT count(*) FROM (SELECT v.id FROM v_raw_stock v
     LEFT JOIN (SELECT raw_material_id, sum(qty_remaining) rem FROM raw_material_batches GROUP BY raw_material_id) b
       ON b.raw_material_id=v.id WHERE v.balance IS DISTINCT FROM coalesce(b.rem,0)) z) AS raw_stock_problems,
  (SELECT count(*) FROM (SELECT v.id FROM v_product_stock v
     LEFT JOIN (SELECT product_id, sum(qty_remaining) rem FROM production GROUP BY product_id) f
       ON f.product_id=v.id WHERE v.balance IS DISTINCT FROM coalesce(f.rem,0)) z) AS finished_stock_problems,
  (SELECT count(*) FROM (SELECT b.id FROM raw_material_batches b
     LEFT JOIN (SELECT batch_id, sum(qty_used) u FROM production_batch_usage GROUP BY batch_id) x ON x.batch_id=b.id
     LEFT JOIN (SELECT batch_id, sum(qty_used) u FROM damage_batch_usage WHERE batch_id IS NOT NULL GROUP BY batch_id) d ON d.batch_id=b.id
     WHERE (b.qty_in-b.qty_remaining) IS DISTINCT FROM (coalesce(x.u,0)+coalesce(d.u,0))) z) AS raw_batch_ledger_problems,
  (SELECT count(*) FROM (SELECT p.id FROM production p
     LEFT JOIN (SELECT production_id, sum(qty_used) u FROM sale_batch_usage GROUP BY production_id) x ON x.production_id=p.id
     LEFT JOIN (SELECT production_id, sum(qty_used) u FROM damage_batch_usage WHERE production_id IS NOT NULL GROUP BY production_id) d ON d.production_id=p.id
     WHERE (p.bundles-p.qty_remaining) IS DISTINCT FROM (coalesce(x.u,0)+coalesce(d.u,0))) z) AS finished_batch_ledger_problems,
  (SELECT count(*) FROM (SELECT d.id FROM damages d
     LEFT JOIN (SELECT damage_id, sum(qty_used) u FROM damage_batch_usage GROUP BY damage_id) x ON x.damage_id=d.id
     WHERE d.qty IS DISTINCT FROM coalesce(x.u,0)) z) AS damage_batch_record_problems;
-- (Note: a finished-goods Physical Count that finds missing bundles lowers
--  qty_remaining without a sale/damage usage row, so those counted-out batches
--  can appear in finished_batch_ledger_problems.)

-- 2) Profit: Dashboard COGS vs invoice-by-invoice COGS must be identical
SELECT (SELECT round(coalesce(sum(cogs_amount),0),2) FROM invoice_lines) AS invoice_lines_cogs,
       (SELECT round(cogs,2) FROM v_pnl) AS dashboard_cogs,
       (SELECT count(*) FROM invoice_lines WHERE qty>0 AND cogs_amount=0) AS zero_cost_sale_lines;

-- 3) Invented stock must never exist again
SELECT count(*) AS auto_shortfall_batches FROM production WHERE batch_ref='Auto (Stock Shortfall)';
SELECT count(*) AS auto_shortfall_raw_batches FROM raw_material_batches WHERE source='Auto (Stock Shortfall)';

-- 4) Money basics
SELECT count(*) AS invoices, sum(net_amount) AS billed, sum(received) AS received, sum(balance_due) AS receivable
FROM v_invoice_summary;

-- 5) Security: public roles must have no grants; RLS on for all tables
SELECT (SELECT count(*) FROM information_schema.role_table_grants
         WHERE table_schema='public' AND grantee IN ('anon','authenticated')) AS public_grants_should_be_0,
       (SELECT count(*) FROM pg_class WHERE relnamespace='public'::regnamespace AND relkind='r' AND relrowsecurity) AS tables_with_rls_should_be_19;
