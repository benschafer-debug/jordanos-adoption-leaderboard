-- Jordano's Foodservice — per-rep adoption scorecard (raw counts) for the leaderboard.
-- Window: trailing 90 days, PLACED_AT between today-90 and today (upper bound guards against
-- the known bogus future-dated order rows). Channels computed fresh from UNIFIED_ORDERS x SMART_ORDER:
--   self_serve = app order (MOBILE/WEB/SUBSCRIPTION), NOT Order Agent, placed by the customer
--   oa         = Order Agent order (matched in SMART_ORDER), rep- or customer-submitted
--   rep        = app order the rep keyed in
--   orders     = Pepper orders (app + OA); offline ERP invoice is excluded
-- Every row also carries the DISTRIBUTOR-WIDE order-grain totals (dw_self, dw_oa, dw_orders),
-- identical on each row, so make_data.py can report the true company-wide team numbers
-- (order-weighted, deduped) rather than an unweighted average of per-rep rates.
WITH oa AS (
  SELECT DISTINCT ORDER_UUID FROM PRODUCTION_ANALYTICS_DB.DBT_PRODUCTION_PEPPER.SMART_ORDER
  WHERE SUPPLIER_UUID='a656335d-0bd0-4246-8f43-ecb59408daf5' AND ORDER_UUID IS NOT NULL
),
emp AS (
  SELECT DISTINCT EMPLOYEE_UUID FROM PRODUCTION_ANALYTICS_DB.DBT_PRODUCTION_SEMANTICS.FCT_PEPPERLYTICS_SALES_REP_ACCOUNT_ACTIVITY
  WHERE DISTRIBUTOR_UUID='a656335d-0bd0-4246-8f43-ecb59408daf5' AND EMPLOYEE_UUID IS NOT NULL
),
ord AS (   -- order-grain channel classification, distributor-wide (deduped, one row per order)
  SELECT uo.ORDER_UUID, uo.CHAT_UUID,
    CASE WHEN oa.ORDER_UUID IS NOT NULL THEN 'oa'
         WHEN emp.EMPLOYEE_UUID IS NOT NULL THEN 'rep'
         ELSE 'self' END AS ch
  FROM PRODUCTION_ANALYTICS_DB.DBT_PRODUCTION_CORE.UNIFIED_ORDERS uo
  LEFT JOIN oa  ON oa.ORDER_UUID=uo.ORDER_UUID
  LEFT JOIN emp ON emp.EMPLOYEE_UUID=uo.ORDER_PLACED_BY_UUID
  WHERE uo.SUPPLIER_UUID='a656335d-0bd0-4246-8f43-ecb59408daf5'
    AND uo.PLACED_SOURCE IN ('MOBILE','WEB','SUBSCRIPTION')
    AND uo.PLACED_AT::date >= DATEADD('day',-90,CURRENT_DATE())
    AND uo.PLACED_AT::date <= CURRENT_DATE()
),
dw AS (   -- distributor-wide totals (order grain) — the true company numbers
  SELECT COUNT_IF(ch='self') AS dw_self, COUNT_IF(ch='oa') AS dw_oa, COUNT(*) AS dw_orders FROM ord
),
acct AS (   -- per-account channel counts
  SELECT CHAT_UUID, COUNT(*) AS orders,
    COUNT_IF(ch='self') AS self_serve_orders, COUNT_IF(ch='oa') AS oa_orders
  FROM ord GROUP BY 1
),
map AS (
  SELECT EMPLOYEE_NAME, CHAT_UUID, MIN(FO_TIMESTAMP) AS first_order
  FROM PRODUCTION_ANALYTICS_DB.DBT_PRODUCTION_PEPPERLYTICS.SALES_REP_ADOPTION
  WHERE DISTRIBUTOR_UUID='a656335d-0bd0-4246-8f43-ecb59408daf5'
    AND NOT (LOWER(EMPLOYEE_NAME) IN ('house','customer chats','unassigned','default','admin','web orders','online orders','web order','online order','pepper')
             OR EMPLOYEE_NAME ILIKE '%(pepper)%')
  GROUP BY 1,2
),
rep AS (
  SELECT m.EMPLOYEE_NAME,
    DATEDIFF('month', MIN(m.first_order), CURRENT_DATE) AS tenure_mo,
    COUNT(DISTINCT m.CHAT_UUID) AS book,
    COUNT(DISTINCT CASE WHEN a.orders>0 THEN m.CHAT_UUID END) AS active_accts,
    COALESCE(SUM(a.orders),0) AS orders,
    COALESCE(SUM(a.self_serve_orders),0) AS self_serve_orders,
    COALESCE(SUM(a.oa_orders),0) AS oa_orders
  FROM map m LEFT JOIN acct a ON a.CHAT_UUID=m.CHAT_UUID
  GROUP BY 1
)
SELECT rep.EMPLOYEE_NAME, rep.tenure_mo, rep.book, rep.active_accts,
  rep.orders, rep.self_serve_orders, rep.oa_orders,
  dw.dw_self, dw.dw_oa, dw.dw_orders,
  CASE WHEN rep.tenure_mo<3 THEN 'New' WHEN rep.orders<20 THEN 'Low volume' ELSE 'Established' END AS segment
FROM rep CROSS JOIN dw
WHERE rep.book>=5 AND rep.orders>0
ORDER BY (rep.self_serve_orders+rep.oa_orders)/NULLIF(rep.orders,0) DESC;
