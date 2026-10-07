{{ config(materialized='view') }}

WITH lieux AS (
    SELECT
        l.num_acc,
        c.dep,
        c.lat,
        c.long,
        l.catr,
        l.vma,
        c.com,
        -- granularite_fiable
        CASE WHEN c.lat IS NOT NULL AND c.long IS NOT NULL THEN true ELSE false END AS granularite_fiable,
        -- vma_disponible
        CASE WHEN l.vma IS NOT NULL THEN true ELSE false END AS vma_disponible,
        -- catr_derive (pour simplifier, on mape sur le type de route)
        CASE
            WHEN l.catr = 1 THEN 'Autoroute'
            WHEN l.catr = 2 THEN 'Nationale'
            WHEN l.catr = 3 THEN 'Departementale'
            WHEN l.catr = 4 THEN 'Communale'
            ELSE 'Autre'
        END AS catr_derive,
        u.grav,
        CASE WHEN u.grav IN (2, 3) THEN 1 ELSE 0 END as is_grave
    FROM {{ ref('stg_lieux') }} l
    JOIN {{ ref('stg_caracteristiques') }} c ON l.num_acc = c.num_acc
    LEFT JOIN {{ ref('stg_usagers') }} u ON l.num_acc = u.num_acc
),

stats_dep AS (
    SELECT
        dep,
        COUNT(DISTINCT num_acc) AS nb_accidents_zone,
        SUM(is_grave)::FLOAT / NULLIF(COUNT(*), 0) AS taux_gravite_zone
    FROM lieux
    GROUP BY dep
),

stats_catr AS (
    SELECT
        catr,
        SUM(is_grave)::FLOAT / NULLIF(COUNT(*), 0) AS risque_relatif_catr
    FROM lieux
    GROUP BY catr
)

SELECT DISTINCT
    l.num_acc,
    l.granularite_fiable,
    l.vma_disponible,
    l.catr_derive,
    COALESCE(sd.nb_accidents_zone, 0) AS nb_accidents_zone,
    COALESCE(sd.taux_gravite_zone, 0.0) AS taux_gravite_zone,
    COALESCE(sc.risque_relatif_catr, 0.0) AS risque_relatif_catr
FROM lieux l
LEFT JOIN stats_dep sd ON l.dep = sd.dep
LEFT JOIN stats_catr sc ON l.catr = sc.catr
