{{ config(materialized='table') }}

WITH base AS (
    SELECT
        a.usager_id,
        a.num_acc,
        a.place,
        a.catu,
        a.grav,
        a.sexe,
        a.an_nais,
        a.trajet,
        a.is_metropole,
        a.source_year,
        a.catv,
        a.lum,
        a.atm,
        a.an, a.mois, a.jour,
        -- Target
        CASE WHEN a.grav IN (2, 3) THEN 1 ELSE 0 END AS is_grave,
        make_date(a.an, a.mois, a.jour)::timestamp AS event_timestamp
    FROM {{ ref('int_accidents_joined') }} a
),

grav_max AS (
    SELECT
        num_acc,
        MAX(CASE WHEN grav IN (2, 3) THEN 1 ELSE 0 END) AS grav_max_accident
    FROM base
    GROUP BY num_acc
)

SELECT
    b.usager_id,
    b.num_acc,
    b.place,
    b.catu,
    b.grav,
    b.sexe,
    b.an_nais,
    b.trajet,
    b.is_metropole,
    b.is_grave,
    b.event_timestamp,

    -- Feature: age_bucket
    CASE
        WHEN (b.source_year - b.an_nais) <= 18 THEN '0-18'
        WHEN (b.source_year - b.an_nais) BETWEEN 19 AND 25 THEN '19-25'
        WHEN (b.source_year - b.an_nais) BETWEEN 26 AND 35 THEN '26-35'
        WHEN (b.source_year - b.an_nais) BETWEEN 36 AND 50 THEN '36-50'
        WHEN (b.source_year - b.an_nais) BETWEEN 51 AND 65 THEN '51-65'
        ELSE '65+'
    END AS age_bucket,

    -- Feature: is_motorise
    CASE WHEN b.catv NOT IN (1, 60) AND b.catu != 3 THEN true ELSE false END AS is_motorise,

    -- Feature T0: lum_calculee
    CASE
        WHEN b.lum IN (1, 2) THEN 'Jour'
        WHEN b.lum IN (3, 4, 5) THEN 'Nuit'
        ELSE 'Inconnu'
    END AS lum_calculee,

    -- Feature T0: atm_simplifie
    CASE
        WHEN b.atm = 1 THEN 'Normal'
        WHEN b.atm IN (2, 3, 4, 5, 6, 7) THEN 'Intemperies'
        ELSE 'Autre'
    END AS atm_simplifie,

    -- Features Temporelles (Famille B)
    t.hrmn_valide,
    t.creneau_2h,
    t.jour_semaine,
    t.is_ferie,
    t.is_vacances_scolaires,

    -- Features Lieux & Infrastructure (Famille A & C)
    l.granularite_fiable,
    l.vma_disponible,
    l.catr_derive,
    l.nb_accidents_zone,
    l.taux_gravite_zone,
    l.risque_relatif_catr,

    -- Feature Secours: grav_max_accident
    gm.grav_max_accident,

    -- Feature Alerte Météo (Mock pour T0)
    -- En réalité, `risque_historique_meteo` serait pré-calculé par commune. Ici on simplifie:
    CASE WHEN b.atm IN (2, 3, 4, 5, 6, 7) THEN true ELSE false END AS risque_historique_meteo

FROM base b
LEFT JOIN {{ ref('int_features_temporelles') }} t ON b.num_acc = t.num_acc
LEFT JOIN {{ ref('int_features_lieux') }} l ON b.num_acc = l.num_acc
LEFT JOIN grav_max gm ON b.num_acc = gm.num_acc
