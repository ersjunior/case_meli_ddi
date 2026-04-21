WITH source AS (

    SELECT * FROM {{ source('raw', 'tb_ddi') }}

),

typed AS (

    SELECT
        username,
        TO_DATE(NULLIF(TRIM(date_month::text), ''), 'YYYY-MM') AS date_month,
        NULLIF(TRIM(user_classification), '') AS user_classification,
        CAST(is_data_user AS BOOLEAN) AS is_data_user

    FROM source

    WHERE username IS NOT NULL
      AND date_month IS NOT NULL

),

deduped AS (

    SELECT DISTINCT ON (username, date_month)
        username,
        date_month,
        user_classification,
        is_data_user
    FROM typed
    ORDER BY
        username,
        date_month,
        is_data_user DESC NULLS LAST,
        user_classification ASC NULLS LAST

)

SELECT * FROM deduped
