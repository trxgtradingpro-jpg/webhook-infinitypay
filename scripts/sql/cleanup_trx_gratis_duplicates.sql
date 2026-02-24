-- Cleanup for duplicate TRX GRATIS paid orders created on the same day
-- Scope: keeps one canonical order per (nome, email, telefone, day) and removes extra rows.
-- Safe flow:
-- 1) Run only the preview query section first.
-- 2) Run the transaction section and inspect counts.
-- 3) COMMIT (or ROLLBACK if anything looks wrong).

-- =====================================================
-- PREVIEW (dry-run): duplicate groups that will be affected
-- =====================================================
WITH normalized AS (
    SELECT
        order_id,
        LOWER(BTRIM(COALESCE(nome, ''))) AS nome_key,
        LOWER(BTRIM(COALESCE(email, ''))) AS email_key,
        REGEXP_REPLACE(COALESCE(telefone, ''), '\D', '', 'g') AS phone_key,
        DATE(created_at) AS day_key,
        created_at,
        COALESCE(whatsapp_mensagens_enviadas, 0) AS wa_msgs,
        COALESCE(whatsapp_enviado, FALSE) AS wa_sent
    FROM orders
    WHERE plano = 'trx-gratis'
      AND status = 'PAGO'
      AND COALESCE(BTRIM(email), '') <> ''
),
ranked AS (
    SELECT
        n.*,
        COUNT(*) OVER (
            PARTITION BY n.nome_key, n.email_key, n.phone_key, n.day_key
        ) AS grp_count
    FROM normalized n
)
SELECT
    nome_key,
    email_key,
    phone_key,
    day_key,
    grp_count AS total_orders,
    ARRAY_AGG(order_id ORDER BY created_at, order_id) AS order_ids
FROM ranked
WHERE grp_count > 1
GROUP BY nome_key, email_key, phone_key, day_key, grp_count
ORDER BY day_key DESC, total_orders DESC, email_key;

-- =====================================================
-- EXECUTION
-- =====================================================
BEGIN;

CREATE TEMP TABLE tmp_trx_gratis_dedupe_map AS
WITH normalized AS (
    SELECT
        order_id,
        LOWER(BTRIM(COALESCE(nome, ''))) AS nome_key,
        LOWER(BTRIM(COALESCE(email, ''))) AS email_key,
        REGEXP_REPLACE(COALESCE(telefone, ''), '\D', '', 'g') AS phone_key,
        DATE(created_at) AS day_key,
        created_at,
        COALESCE(whatsapp_mensagens_enviadas, 0) AS wa_msgs,
        COALESCE(whatsapp_enviado, FALSE) AS wa_sent
    FROM orders
    WHERE plano = 'trx-gratis'
      AND status = 'PAGO'
      AND COALESCE(BTRIM(email), '') <> ''
),
ranked AS (
    SELECT
        n.*,
        ROW_NUMBER() OVER (
            PARTITION BY n.nome_key, n.email_key, n.phone_key, n.day_key
            ORDER BY n.wa_msgs DESC, n.wa_sent DESC, n.created_at ASC, n.order_id ASC
        ) AS rn
    FROM normalized n
),
keepers AS (
    SELECT
        nome_key,
        email_key,
        phone_key,
        day_key,
        order_id AS keep_order_id
    FROM ranked
    WHERE rn = 1
),
drops AS (
    SELECT
        nome_key,
        email_key,
        phone_key,
        day_key,
        order_id AS drop_order_id
    FROM ranked
    WHERE rn > 1
)
SELECT
    k.keep_order_id,
    d.drop_order_id
FROM keepers k
JOIN drops d
  ON d.nome_key = k.nome_key
 AND d.email_key = k.email_key
 AND d.phone_key = k.phone_key
 AND d.day_key = k.day_key;

CREATE INDEX idx_tmp_trx_gratis_drop ON tmp_trx_gratis_dedupe_map(drop_order_id);
CREATE INDEX idx_tmp_trx_gratis_keep ON tmp_trx_gratis_dedupe_map(keep_order_id);

SELECT
    COUNT(*) AS duplicates_to_remove,
    COUNT(DISTINCT keep_order_id) AS affected_groups
FROM tmp_trx_gratis_dedupe_map;

-- Preserve non-unique references by pointing to the canonical order_id.
UPDATE analytics_funnel_events a
SET order_id = m.keep_order_id
FROM tmp_trx_gratis_dedupe_map m
WHERE a.order_id = m.drop_order_id;

UPDATE client_upgrade_leads c
SET order_id = m.keep_order_id
FROM tmp_trx_gratis_dedupe_map m
WHERE c.order_id = m.drop_order_id;

UPDATE affiliate_referrals r
SET first_order_id = m.keep_order_id
FROM tmp_trx_gratis_dedupe_map m
WHERE r.first_order_id = m.drop_order_id;

-- Remove rows that must remain unique per order_id.
DELETE FROM whatsapp_auto_dispatches w
USING tmp_trx_gratis_dedupe_map m
WHERE w.order_id = m.drop_order_id;

DELETE FROM analytics_purchase_events a
USING tmp_trx_gratis_dedupe_map m
WHERE a.order_id = m.drop_order_id;

DELETE FROM affiliate_commissions c
USING tmp_trx_gratis_dedupe_map m
WHERE c.order_id = m.drop_order_id;

-- Remove duplicate orders.
DELETE FROM orders o
USING tmp_trx_gratis_dedupe_map m
WHERE o.order_id = m.drop_order_id;

-- Final validation inside the same transaction.
WITH normalized AS (
    SELECT
        LOWER(BTRIM(COALESCE(nome, ''))) AS nome_key,
        LOWER(BTRIM(COALESCE(email, ''))) AS email_key,
        REGEXP_REPLACE(COALESCE(telefone, ''), '\D', '', 'g') AS phone_key,
        DATE(created_at) AS day_key
    FROM orders
    WHERE plano = 'trx-gratis'
      AND status = 'PAGO'
      AND COALESCE(BTRIM(email), '') <> ''
),
ranked AS (
    SELECT
        COUNT(*) AS grp_count
    FROM normalized
    GROUP BY nome_key, email_key, phone_key, day_key
)
SELECT COALESCE(SUM(CASE WHEN grp_count > 1 THEN 1 ELSE 0 END), 0) AS remaining_duplicate_groups
FROM ranked;

-- Default safety mode:
ROLLBACK;
-- To apply de-duplication for real, replace the line above with:
-- COMMIT;
