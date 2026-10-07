WITH vehicules AS (
    SELECT DISTINCT
        catv, choc, manv, motor
    FROM {{ ref('int_accidents_joined') }}
)
SELECT
    ROW_NUMBER() OVER (ORDER BY catv, choc, manv, motor) AS vehicule_key,
    catv,
    CASE
        WHEN catv IN (1, 2, 3) THEN 'Deux-roues'
        WHEN catv = 7 THEN 'Véhicule léger'
        WHEN catv IN (13, 14, 15, 16, 17) THEN 'Poids lourd'
        ELSE 'Autre'
    END AS catv_label,
    choc,
    manv,
    CASE WHEN motor IS NOT NULL AND motor > 0 THEN TRUE ELSE FALSE END AS is_motorise,
    CASE WHEN catv IN (1, 2, 3, 30, 31, 32, 33, 34) THEN TRUE ELSE FALSE END AS is_deux_roues,
    CASE WHEN catv IN (13, 14, 15, 16, 17, 37, 38, 39, 40) THEN TRUE ELSE FALSE END AS is_lourd
FROM vehicules
