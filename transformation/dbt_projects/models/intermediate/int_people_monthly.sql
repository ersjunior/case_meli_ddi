WITH months AS (

    SELECT DISTINCT date_month
    FROM {{ ref('stg_ddi') }}

),

people AS (

    SELECT * FROM {{ ref('stg_people_history') }}

),

month_bounds AS (

    SELECT
        date_month,
        date_month AS month_start,
        (date_trunc('month', date_month::timestamp) + interval '1 month - 1 day')::date AS month_end
    FROM months

),

eligible AS (

    SELECT
        mb.date_month,
        p.username,
        p.tim_day,
        p.start_date,
        p.end_date,
        p.country,
        p.site,
        p.department,
        p.division,
        p.function,
        ROW_NUMBER() OVER (
            PARTITION BY p.username, mb.date_month
            ORDER BY p.tim_day DESC
        ) AS rn

    FROM month_bounds mb
    INNER JOIN people p
        ON p.start_date <= mb.month_end
       AND COALESCE(p.end_date, DATE '9999-12-31') >= mb.month_start
       AND NOT (
            p.division = 'Shipping'
            AND p.function = 'Representative'
        )

)

SELECT
    date_month,
    username,
    start_date,
    end_date,
    country,
    site,
    department,
    division,
    function
FROM eligible
WHERE rn = 1
