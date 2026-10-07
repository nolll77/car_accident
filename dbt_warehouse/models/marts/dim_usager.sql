WITH usagers AS (
    SELECT DISTINCT
        catu, sexe, an_nais, trajet
    FROM {{ ref('int_accidents_joined') }}
)
SELECT
    ROW_NUMBER() OVER (ORDER BY catu, sexe, an_nais, trajet) AS usager_key,
    catu,
    sexe,
    (2024 - an_nais) AS age,
    CASE
        WHEN (2024 - an_nais) < 18 THEN '<18'
        WHEN (2024 - an_nais) BETWEEN 18 AND 25 THEN '18-25'
        WHEN (2024 - an_nais) BETWEEN 26 AND 40 THEN '26-40'
        WHEN (2024 - an_nais) BETWEEN 41 AND 60 THEN '41-60'
        ELSE '>60'
    END AS age_bucket,
    trajet
FROM usagers
