-- Ensure no accident dates are in the future
SELECT *
FROM {{ ref('fact_accident_usager') }}
WHERE annee > EXTRACT(YEAR FROM CURRENT_DATE)
