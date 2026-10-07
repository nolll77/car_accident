WITH source AS (
    SELECT * FROM {{ source('baac_raw', 'raw_caracteristiques') }}
)
SELECT
    num_acc,
    CAST(an AS INTEGER) AS an,
    CAST(mois AS INTEGER) AS mois,
    CAST(jour AS INTEGER) AS jour,
    hrmn,
    CAST(lum AS INTEGER) AS lum,
    dep,
    com,
    CAST(agg AS INTEGER) AS agg,
    CAST("int" AS INTEGER) AS type_intersection,
    CAST(atm AS INTEGER) AS atm,
    CAST(col AS INTEGER) AS col,
    adr,
    CAST(lat AS FLOAT) AS lat,
    CAST(long AS FLOAT) AS long,
    CAST(source_year AS INTEGER) AS source_year,
    CAST(is_metropole AS BOOLEAN) AS is_metropole,
    territoire
FROM source
