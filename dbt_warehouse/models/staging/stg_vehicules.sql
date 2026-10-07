WITH source AS (
    SELECT * FROM {{ source('baac_raw', 'raw_vehicules') }}
)
SELECT
    num_acc,
    id_vehicule,
    num_veh,
    CAST(catv AS INTEGER) AS catv,
    CAST(choc AS INTEGER) AS choc,
    CAST(manv AS INTEGER) AS manv,
    CAST(motor AS INTEGER) AS motor
FROM source
