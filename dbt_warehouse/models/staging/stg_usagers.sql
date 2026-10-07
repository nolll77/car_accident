WITH source AS (
    SELECT * FROM {{ source('baac_raw', 'raw_usagers') }}
)
SELECT
    num_acc,
    id_vehicule,
    num_veh,
    usager_id,
    CAST(place AS INTEGER) AS place,
    CAST(catu AS INTEGER) AS catu,
    CAST(grav AS INTEGER) AS grav,
    CAST(sexe AS INTEGER) AS sexe,
    CAST(an_nais AS INTEGER) AS an_nais,
    CAST(trajet AS INTEGER) AS trajet,
    CAST(secu1 AS INTEGER) AS secu1
FROM source
