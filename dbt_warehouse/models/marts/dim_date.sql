WITH dates AS (
    SELECT DISTINCT
        an, mois, jour
    FROM {{ ref('int_accidents_joined') }}
)
SELECT
    ROW_NUMBER() OVER (ORDER BY an, mois, jour) AS date_key,
    an AS annee,
    mois,
    jour,
    MAKE_DATE(an, mois, jour) AS date_complete,
    EXTRACT(DOW FROM MAKE_DATE(an, mois, jour)) AS jour_semaine,
    CASE WHEN EXTRACT(DOW FROM MAKE_DATE(an, mois, jour)) IN (0, 6) THEN TRUE ELSE FALSE END AS is_weekend,
    CASE
        WHEN mois IN (12, 1, 2) THEN 'Hiver'
        WHEN mois IN (3, 4, 5) THEN 'Printemps'
        WHEN mois IN (6, 7, 8) THEN 'Été'
        ELSE 'Automne'
    END AS saison
FROM dates
WHERE an IS NOT NULL AND mois IS NOT NULL AND jour IS NOT NULL
  AND jour <= 28
