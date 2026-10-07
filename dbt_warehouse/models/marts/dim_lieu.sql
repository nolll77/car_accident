WITH lieux AS (
    SELECT DISTINCT
        dep, com, catr, circ, surf, situ, geo_level, territoire
    FROM {{ ref('int_accidents_joined') }}
)
SELECT
    ROW_NUMBER() OVER (ORDER BY dep, com, catr, circ, surf, situ, geo_level, territoire) AS lieu_key,
    dep,
    com,
    catr,
    CASE
        WHEN catr = 1 THEN 'Autoroute'
        WHEN catr = 2 THEN 'Route nationale'
        WHEN catr = 3 THEN 'Route départementale'
        WHEN catr = 4 THEN 'Voie communale'
        ELSE 'Autre'
    END AS catr_label,
    circ,
    surf,
    situ,
    geo_level,
    territoire
FROM lieux
