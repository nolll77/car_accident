{{ config(materialized='view') }}

WITH accidents AS (
    SELECT
        num_acc,
        make_date(an, mois, jour)::timestamp AS event_timestamp,
        make_date(an, mois, jour) AS event_date,
        hrmn,
        -- hrmn_valide: on considère valide si on a réussi à parser l'heure proprement,
        -- ou ici on simplifie en flaggant les années 2021-2022 si besoin,
        -- mais le harmonizer a mis hrmn = NULL ou conservé HH:MM
        CASE WHEN hrmn IS NOT NULL THEN true ELSE false END AS hrmn_valide,
        -- creneau_2h: par exemple '08:00-10:00'
        CASE
            WHEN hrmn IS NOT NULL AND split_part(hrmn, ':', 1) != '' THEN
                CAST(split_part(hrmn, ':', 1) AS INTEGER) / 2 * 2 || ':00-' || (CAST(split_part(hrmn, ':', 1) AS INTEGER) / 2 * 2 + 2) || ':00'
            ELSE 'Inconnu'
        END AS creneau_2h
    FROM {{ ref('stg_caracteristiques') }}
),

calendrier AS (
    SELECT
        date::date AS cal_date,
        jour_semaine,
        is_ferie,
        is_vacances_scolaires
    FROM {{ ref('seed_calendrier') }}
)

SELECT
    a.num_acc,
    a.event_timestamp,
    a.hrmn_valide,
    a.creneau_2h,
    c.jour_semaine,
    c.is_ferie,
    c.is_vacances_scolaires
FROM accidents a
LEFT JOIN calendrier c ON a.event_date = c.cal_date
