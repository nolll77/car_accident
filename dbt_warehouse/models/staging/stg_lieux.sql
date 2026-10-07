WITH source AS (
    SELECT * FROM {{ source('baac_raw', 'raw_lieux') }}
)
SELECT
    num_acc,
    CAST(catr AS INTEGER) AS catr,
    CAST(circ AS INTEGER) AS circ,
    CAST(nbv AS INTEGER) AS nbv,
    CAST(surf AS INTEGER) AS surf,
    CAST(situ AS INTEGER) AS situ,
    voie,
    prof,
    CAST(CAST(vma AS FLOAT) AS INTEGER) AS vma,
    geo_level
FROM source
