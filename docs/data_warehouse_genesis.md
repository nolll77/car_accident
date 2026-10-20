# Génèse du Data Warehouse MLOps (Monitoring & KPIs)

> [!NOTE]
> **Rôles de ce document "Génèse" :**
> 1. **Boussole architecturale :** Fixer le "Pourquoi" (la philosophie conceptuelle) pour guider la technique.
> 2. **Outil de vulgarisation :** Expliquer simplement le projet à quelqu'un d'extérieur au domaine de la data ou du code.
> 3. **Support de défense & Onboarding :** Justifier nos choix techniques (ex: pourquoi faire un schéma en étoile) lors d'une présentation ou de l'intégration d'un collaborateur.
>
> *Sujet de ce document :* La philosophie de construction de la brique analytique (Data Warehouse) comme sous-produit essentiel pour le monitoring en production.

## 1. Le problème : L'explosion combinatoire et le besoin de monitoring

Une fois notre modèle ML en production, nous avons besoin de suivre ses performances et la qualité des données entrantes (Data Drift). Nous devons répondre à des questions macroscopiques comme :
- *Quel est le taux de mortalité ce mois-ci par rapport à l'an dernier ?*
- *Y a-t-il une hausse des accidents graves sur les routes départementales ?*

Si on essaie de répondre à ces questions en interrogeant directement la table d'entraînement (la *Feature Matrix* à grain "Usager"), on fausse les calculs.

> [!WARNING]
> **Le piège de la duplication (Grain mismatch)**
> Si un accident implique 2 lieux documentés et 4 véhicules avec plusieurs usagers, une jointure naïve va multiplier les lignes (ex: 2 × 4 = 8 lignes d'accidents fictives). Compter les "accidents" sur la table ML donnera un chiffre artificiellement gonflé.

## 2. La solution : Le schéma en étoile et la table de faits

Pour les calculs macroscopiques et le monitoring (BI), la granularité ne doit pas être "l'Usager", mais **l'Accident**. C'est le rôle du Data Warehouse.

Plutôt que d'utiliser la grande table aplatie, nous créons un **Schéma en Étoile** composé de :

### A. Les Dimensions (Les 5 axes d'analyse avancés)
- **Dim_Date** : Évolution temporelle (avec flag `weekend`, `periode_jour`).
- **Dim_Lieu** : Localisation et infra (enrichi avec `zone_danger`).
- **Dim_Meteo** : Conditions météo et lumière (Feature group séparé).
- **Dim_Vehicule** : Types de véhicules (avec flag `is_motorise`, `is_deux_roues`).
- **Dim_Usager** : Profils de victimes (avec `age_bucket`).

### B. La Table de Faits (FACT_ACCIDENT_USAGER)
Dans une vision "Niveau Entreprise", la table de faits pour l'analyse fine (et pour l'entraînement ML) descend au grain de l'**Usager** : 1 ligne = 1 usager impliqué dans 1 accident.

C'est cette table centrale (qui contient les clés étrangères vers toutes les dimensions) qui porte la **mesure de la gravité** et les métriques agrégées (ex: `nb_vehicules_accident`, `nb_usagers_accident`).

> *Note : Pour les macros-KPIs purs (ex: comptage strict du nombre d'accidents), on utilisera une vue agrégée (FACT_ACCIDENT au grain "Accident") pour éviter l'explosion combinatoire.*

## 3. L'usage MLOps et Optimisations

Le choix technique acté pour ce Data Warehouse de monitoring est **PostgreSQL**, qui sera déployé de manière reproductible via **Docker Compose**.
Les transformations brutes vers le modèle en étoile seront effectuées par **dbt (Data Build Tool)**. En utilisant dbt, nous implémentons l'approche *Analytics as Code*, garantissant la traçabilité des transformations et la possibilité de lancer des tests déclaratifs (`dbt tests`) sur la base PostgreSQL.
Il sera ensuite branché à un outil de dashboarding open-source d'entreprise (**Apache Superset**) pour créer la console de monitoring du MLOps Engineer (Data Observability).

**Défense d'Architecture (PostgreSQL vs Lakehouse) :**
Nous rejetons catégoriquement la mise en place d'une architecture *Lakehouse* (MinIO + Apache Iceberg + Trino). Bien qu'il s'agisse de l'état de l'art pour les environnements Big Data multi-pétaoctets (type Netflix ou Uber), déployer un moteur de requêtes distribué et un Metastore pour traiter 4 fichiers CSV de 50 Mo mis à jour annuellement est un anti-pattern absolu (Sur-ingénierie extrême). PostgreSQL est parfaitement dimensionné, infiniment plus simple à maintenir et suffisant pour nos besoins de requêtage MLOps.

**Défense d'Architecture (Étoile vs Flocon) :**
Nous optons pour un **Schéma en Étoile strict**. Nous refusons catégoriquement la sur-normalisation en "Flocon" (Snowflake schema) qui consisterait à éclater la table `DIM_CONDITIONS` en micro-tables (`DIM_METEO`, `DIM_LUMIERE`, `DIM_INTERSECTION`). C'est inutilement lourd pour notre volume et complexifie les requêtes de monitoring.

**Optimisations prévues :**
- **Partitionnement** de la table de faits par année (pour gérer le volume historique 2005-2024).
- **Indexation** sur les clés de jointure et la gravité pour des requêtes analytiques rapides.
