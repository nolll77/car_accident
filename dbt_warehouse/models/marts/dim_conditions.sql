WITH conditions AS (
    SELECT DISTINCT
        lum, atm
    FROM {{ ref('int_accidents_joined') }}
)
SELECT
    ROW_NUMBER() OVER (ORDER BY lum, atm) AS conditions_key,
    lum,
    atm,
    CASE WHEN lum IN (3, 4, 5) THEN TRUE ELSE FALSE END AS is_night,
    CASE WHEN atm IN (2, 3) THEN TRUE ELSE FALSE END AS is_rain,
    CASE
        WHEN atm = 1 THEN 'Normale'
        WHEN atm = 2 THEN 'Pluie légère'
        WHEN atm = 3 THEN 'Pluie forte'
        WHEN atm = 4 THEN 'Neige'
        WHEN atm = 5 THEN 'Brouillard'
        ELSE 'Autre'
    END AS atm_simplifie
FROM conditions
