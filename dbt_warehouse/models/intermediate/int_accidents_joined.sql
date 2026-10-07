WITH usagers AS (SELECT * FROM {{ ref('stg_usagers') }}),
vehicules AS (SELECT * FROM {{ ref('stg_vehicules') }}),
lieux AS (SELECT * FROM {{ ref('stg_lieux') }}),
caracteristiques AS (SELECT * FROM {{ ref('stg_caracteristiques') }})

SELECT
    u.*,
    v.catv, v.choc, v.manv, v.motor,
    l.catr, l.circ, l.nbv, l.surf, l.situ, l.voie, l.prof, l.geo_level,
    c.an, c.mois, c.jour, c.hrmn, c.lum, c.dep, c.com, c.agg, c.type_intersection, c.atm, c.col, c.adr,
    c.lat, c.long, c.source_year, c.is_metropole, c.territoire
FROM usagers u
LEFT JOIN vehicules v ON u.num_acc = v.num_acc AND u.id_vehicule = v.id_vehicule
LEFT JOIN lieux l ON u.num_acc = l.num_acc
LEFT JOIN caracteristiques c ON u.num_acc = c.num_acc
