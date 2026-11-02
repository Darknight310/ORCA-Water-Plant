# 2026-11-02 damage date correction and full-line editing

## Live data correction

The only damage entry then in the database was:

- Damage ID: 1
- Item: 500ml Pure Bottle
- Quantity: 192
- Wrong date: 2026-11-20
- Corrected date: 2026-10-20

Only `damages.damage_date` was changed for that row. Its quantity, batch and
locked unit cost were not changed.

## Database change

Migration `add_damage_batch_usage` added `public.damage_batch_usage`.
It records every exact raw-material batch or production batch used by a damage,
including quantity and unit cost.

Damage #1 was backfilled exactly: 192 units from raw-material batch #14 at
PKR 13.8 per unit. That material had only that batch, and the batch arithmetic
also reconciles exactly: 3,600 in - 3,396 used in production - 192 damaged -
12 remaining = 0 unexplained.

## Why the table matters

Before this table, a damage only remembered the first batch it used. That made
changing a damage quantity/item unsafe when it had spanned more than one batch.
Now editing or deleting a damage can:

1. Put the old quantity back into the exact batch(es).
2. Take the corrected quantity again, oldest batch first.
3. Recalculate the damage unit cost and loss from the real batches.

The table has Row Level Security enabled and follows the existing security
model: no anon/authenticated grants; service_role only.
