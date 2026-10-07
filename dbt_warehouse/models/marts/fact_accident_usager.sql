SELECT
    usager_id,
    num_acc,
    dep,
    an AS annee,
    mois,
    jour,
    grav,
    CASE WHEN grav IN (2, 3) THEN 1 ELSE 0 END AS is_grave,
    catu,
    catv,
    lum,
    atm,
    col,
    catr,
    source_year,
    is_metropole,
    make_date(an, mois, jour)::timestamp AS event_timestamp
FROM {{ ref('int_accidents_joined') }}
