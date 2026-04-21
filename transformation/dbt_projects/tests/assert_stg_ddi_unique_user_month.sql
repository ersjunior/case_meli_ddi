SELECT
    username,
    date_month,
    COUNT(*) AS cnt
FROM {{ ref('stg_ddi') }}
GROUP BY 1, 2
HAVING COUNT(*) > 1
