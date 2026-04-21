WITH base AS (

    SELECT
        username,
        date_month,
        is_data_user,

        ROW_NUMBER() OVER (PARTITION BY username ORDER BY date_month) -
        ROW_NUMBER() OVER (PARTITION BY username, is_data_user ORDER BY date_month) AS grp

    FROM {{ ref('stg_ddi') }}

),

streaks AS (

    SELECT
        username,
        date_month,
        is_data_user,
        COUNT(*) OVER (PARTITION BY username, grp) AS streak

    FROM base
    WHERE is_data_user IS TRUE

),

final AS (

    SELECT
        username,
        date_month,
        CASE WHEN streak >= 3 THEN TRUE ELSE FALSE END AS is_potential_user

    FROM streaks

)

SELECT * FROM final
