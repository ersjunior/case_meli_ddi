WITH source AS (

    SELECT * FROM {{ source('raw', 'tb_people_history') }}

),

cleaned AS (

    SELECT
        username,
        CAST(tim_day AS DATE) AS tim_day,
        CAST(start_date AS DATE) AS start_date,
        CAST(end_date AS DATE) AS end_date,
        country,
        site,
        department,
        division,
        function

    FROM source

)

SELECT * FROM cleaned
