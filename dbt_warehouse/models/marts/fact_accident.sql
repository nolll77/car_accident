SELECT
    num_acc,
    MIN(an) AS annee,
    MIN(mois) AS mois,
    MIN(jour) AS jour,
    MIN(dep) AS dep,
    COUNT(*) AS nb_usagers,
    COUNT(DISTINCT id_vehicule) AS nb_vehicules,
    SUM(CASE WHEN grav = 2 THEN 1 ELSE 0 END) AS nb_tues,
    SUM(CASE WHEN grav IN (2, 3) THEN 1 ELSE 0 END) AS nb_graves,
    SUM(CASE WHEN grav = 4 THEN 1 ELSE 0 END) AS nb_blesses_legers,
    MAX(grav) AS gravite_max,
    MIN(is_metropole::int)::boolean AS is_metropole
FROM {{ ref('int_accidents_joined') }}
GROUP BY num_acc
