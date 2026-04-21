WITH people AS (

    SELECT * FROM {{ ref('int_people_monthly') }}

),

ddi AS (

    SELECT * FROM {{ ref('stg_ddi') }}

),

streak AS (

    SELECT
        username,
        date_month,
        is_potential_user
    FROM {{ ref('int_user_streak') }}

),

final AS (

    SELECT
        p.username,
        p.date_month,
        p.site,
        p.division,
        p.department,
        COALESCE(ddi.user_classification, 'Sem registro DDI') AS user_classification,
        COALESCE(ddi.is_data_user, FALSE) AS is_data_user,
        COALESCE(s.is_potential_user, FALSE) AS is_potential_user,
        (ddi.username IS NOT NULL) AS has_ddi_row,
        TRUE AS is_active

    FROM people p
    LEFT JOIN ddi
        ON p.username = ddi.username
       AND p.date_month = ddi.date_month
    LEFT JOIN streak s
        ON p.username = s.username
       AND p.date_month = s.date_month

)

SELECT * FROM final
