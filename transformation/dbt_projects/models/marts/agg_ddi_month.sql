WITH fct AS (

    SELECT * FROM {{ ref('fct_user_month') }}

),

dept_month AS (

    SELECT
        date_month,
        site,
        division,
        department,
        COUNT(DISTINCT username) AS active_collaborators_total,
        COUNT(DISTINCT CASE WHEN has_ddi_row THEN username END) AS collaborators_with_ddi

    FROM fct
    GROUP BY 1, 2, 3, 4

),

agg AS (

    SELECT
        date_month,
        site,
        division,
        department,
        user_classification,
        COUNT(DISTINCT username) AS active_collaborators,
        COUNT(DISTINCT CASE WHEN is_data_user THEN username END) AS data_driven_users,
        COUNT(DISTINCT CASE WHEN is_potential_user THEN username END) AS potential_users

    FROM fct
    GROUP BY 1, 2, 3, 4, 5

),

with_cov AS (

    SELECT
        a.*,
        dm.collaborators_with_ddi * 100.0 / NULLIF(dm.active_collaborators_total, 0) AS coverage_rate

    FROM agg a
    INNER JOIN dept_month dm
        ON a.date_month = dm.date_month
       AND a.site = dm.site
       AND a.division = dm.division
       AND a.department = dm.department

),

with_share AS (

    SELECT
        *,
        potential_users * 100.0 / NULLIF(
            SUM(potential_users) OVER (
                PARTITION BY date_month, site, division, department
            ),
            0
        ) AS share_per_ddi_classification

    FROM with_cov

),

dept_totals AS (

    SELECT
        date_month,
        site,
        division,
        department,
        SUM(potential_users) AS total_potential_in_dept

    FROM with_share
    GROUP BY 1, 2, 3, 4

),

div_median AS (

    SELECT
        date_month,
        site,
        division,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_potential_in_dept) AS median_dept_potential

    FROM dept_totals
    GROUP BY 1, 2, 3

),

final AS (

    SELECT
        w.*,
        (w.potential_users - dm.median_dept_potential) AS gap_to_target,
        CASE
            WHEN LAG(w.potential_users) OVER (
                PARTITION BY w.site, w.division, w.department, w.user_classification
                ORDER BY w.date_month
            ) IS NULL THEN NULL
            ELSE (
                (w.potential_users::numeric - LAG(w.potential_users) OVER (
                    PARTITION BY w.site, w.division, w.department, w.user_classification
                    ORDER BY w.date_month
                ))
                / NULLIF(
                    LAG(w.potential_users) OVER (
                        PARTITION BY w.site, w.division, w.department, w.user_classification
                        ORDER BY w.date_month
                    ),
                    0
                )
            ) * 100.0
        END AS transition_rate

    FROM with_share w
    INNER JOIN div_median dm
        ON w.date_month = dm.date_month
       AND w.site = dm.site
       AND w.division = dm.division

)

SELECT * FROM final
