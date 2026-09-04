-- Jordano's Foodservice — per-rep adoption scorecard (raw counts) for the leaderboard.
-- Window: trailing 90 days. Channels computed fresh from UNIFIED_ORDERS x SMART_ORDER.
--   self_serve_orders = app order (MOBILE/WEB/SUBSCRIPTION), NOT Order Agent, placed by the customer
--   oa_orders         = Order Agent order (matched in SMART_ORDER), rep- or customer-submitted
--   orders            = Pepper orders (app + OA); offline ERP invoice is excluded
-- make_data.py turns these counts into rates, ranks, and team averages -> data.json.
WITH oa AS (
  SELECT DISTINCT ORDER_UUID FROM PRODUCTION_ANALYTICS_DB.DBT_PRODUCTION_PEPPER.SMART_ORDER
  WHERE SUPPLIER_UUID='a656335d-0bd0-4246-8f43-ecb59408daf5' AND ORDER_UUID IS NOT NULL
),
emp AS (
  SELECT DISTINCT EMPLOYEE_UUID FROM PRODUCTION_ANALYTICS_DB.DBT_PRODUCTION_SEMANTICS.FCT_PEPPERLYTICS_SALES_REP_ACCOUNT_ACTIVITY
  WHERE DISTRIBUTOR_UUID='a656335d-0bd0-4246-8f43-ecb59408daf5' AND EMPLOYEE_UUID IS NOT NULL
),
orders AS (
  SELECT uo.CHAT_UUID,
    COUNT(*) AS orders,
    COUNT_IF(oa.ORDER_UUID IS NULL AND emp.EMPLOYEE_UUID IS NULL) AS self_serve_orders,
    COUNT_IF(oa.ORDER_UUID IS NOT NULL) AS oa_orders
  FROM PRODUCTION_ANALYTICS_DB.DBT_PRODUCTION_CORE.UNIFIED_ORDERS uo
  LEFT JOIN oa  ON oa.ORDER_UUID=uo.ORDER_UUID
  LEFT JOIN emp ON emp.EMPLOYEE_UUID=uo.ORDER_PLACED_BY_UUID
  WHERE uo.SUPPLIER_UUID='a656335d-0bd0-4246-8f43-ecb59408daf5'
    AND uo.PLACED_SOURCE IN ('MOBILE','WEB','SUBSCRIPTION')
    AND uo.PLACED_AT::date >= DATEADD('day',-90,CURRENT_DATE())
  GROUP BY 1
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
    COUNT(DISTINCT CASE WHEN o.orders>0 THEN m.CHAT_UUID END) AS active_accts,
    COALESCE(SUM(o.orders),0) AS orders,
    COALESCE(SUM(o.self_serve_orders),0) AS self_serve_orders,
    COALESCE(SUM(o.oa_orders),0) AS oa_orders
  FROM map m LEFT JOIN orders o ON o.CHAT_UUID=m.CHAT_UUID
  GROUP BY 1
)
SELECT EMPLOYEE_NAME, tenure_mo, book, active_accts, orders, self_serve_orders, oa_orders,
  CASE WHEN tenure_mo<3 THEN 'New' WHEN orders<20 THEN 'Low volume' ELSE 'Established' END AS segment
FROM rep
WHERE book>=5 AND orders>0
ORDER BY (self_serve_orders+oa_orders)/NULLIF(orders,0) DESC;
