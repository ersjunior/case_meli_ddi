SELECT
    username,
    date_month,
    COUNT(*) AS cnt
FROM {{ ref('fct_user_month') }}
GROUP BY 1, 2
HAVING COUNT(*) > 1
