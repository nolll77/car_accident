# 🚗 BAAC MLOps — Architecture Complète du Système

> **Projet** : Plateforme MLOps de bout en bout pour l'analyse de l'accidentologie routière française (BAAC).
> **Version** : Octobre 2026
> **Fichiers source** : ~100 fichiers Python, YAML, SQL, Dockerfile
> **Volume de données** : 2,1 millions de lignes (300 000 accidents synthétiques fidèles)
> **Modèles enregistrés** : 3 familles (Classification, Régression, Hybride) dans MLflow
> **Couche Agentique** : Orchestrateur multi-agents autonome avec Policy Engine et Evidence Store

---

## Table des Matières

1. [Vue d'Ensemble de l'Architecture](#1-vue-densemble-de-larchitecture)
2. [Stack Technique Complète](#2-stack-technique-complète)
3. [Infrastructure Conteneurisée (Docker Compose)](#3-infrastructure-conteneurisée-docker-compose)
4. [Pipeline de Données — Architecture Médaillon](#4-pipeline-de-données--architecture-médaillon)
   - 4.1 [Couche Bronze — Génération Synthétique](#41-couche-bronze--génération-synthétique)
   - 4.2 [Couche Silver — Harmonisation Défensive](#42-couche-silver--harmonisation-défensive)
   - 4.3 [Data Contracts (Pandera)](#43-data-contracts-pandera)
   - 4.4 [Couche Gold — Feature Engineering](#44-couche-gold--feature-engineering)
   - 4.5 [Orchestration DVC](#45-orchestration-dvc)
5. [Référentiels de Configuration](#5-référentiels-de-configuration)
6. [Usine d'Entraînement ML & Model Registry](#6-usine-dentraînement-ml--model-registry)
7. [Monitoring de Dérive (Drift)](#7-monitoring-de-dérive-drift)
8. [Couche Agentique — Agentic Control Plane](#8-couche-agentique--agentic-control-plane)
   - 8.1 [Architecture du Core](#81-architecture-du-core)
   - 8.2 [Les 7 Contrats Canoniques](#82-les-7-contrats-canoniques)
   - 8.3 [Machine à États (State Machine)](#83-machine-à-états-state-machine)
   - 8.4 [Policy Engine (Gouvernance)](#84-policy-engine-gouvernance)
   - 8.5 [Adaptateurs d'Observabilité](#85-adaptateurs-dobservabilité)
   - 8.6 [Spécialistes LLM (Agents)](#86-spécialistes-llm-agents)
   - 8.7 [Outils Agentiques (Tools)](#87-outils-agentiques-tools)
   - 8.8 [Evidence Store & Idempotence](#88-evidence-store--idempotence)
   - 8.9 [Orchestrateur Prefect](#89-orchestrateur-prefect)
   - 8.10 [Trust Ledger (Évaluation Shadow)](#810-trust-ledger-évaluation-shadow)
9. [API de Serving (FastAPI)](#9-api-de-serving-fastapi)
10. [Feature Store (Feast)](#10-feature-store-feast)
11. [Data Warehouse (PostgreSQL + dbt)](#11-data-warehouse-postgresql--dbt)
12. [Observabilité & Dashboards](#12-observabilité--dashboards)
13. [Tests & CI/CD](#13-tests--cicd)
14. [Inventaire Exhaustif des Fichiers](#14-inventaire-exhaustif-des-fichiers)
15. [Commandes de Référence](#15-commandes-de-référence)

---

## 1. Vue d'Ensemble de l'Architecture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        AGENTIC CONTROL PLANE                             │
│  ┌─────────┐  ┌──────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │ Signal  │→│ Specialist   │→│ Remediation │→│  Policy Engine   │   │
│  │ (Prom.) │  │ (LLM/Mock)   │  │ Agent       │  │  (YAML Rules)    │   │
│  └────┬────┘  └──────────────┘  └─────────────┘  └────────┬─────────┘   │
│       │                                                     │            │
│       │              State Machine (FSM)                    ▼            │
│       │     DETECTED → INVESTIGATING → DIAGNOSED →    ALLOW/DENY        │
│       │     PLANNED → EXECUTING → RESOLVED                  │            │
│       │                                                     ▼            │
│       │                                          ┌──────────────────┐   │
│       │                                          │  Evidence Store  │   │
│       │                                          │  (JSON append)   │   │
│       │                                          └──────────────────┘   │
└───────┼─────────────────────────────────────────────────────────────────┘
        │
        │ Lit les métriques Prometheus
        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                     MONITORING & DRIFT                                    │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────────────────┐  │
│  │ Evidently AI │→│ prometheus_    │→│ Prometheus + Pushgateway    │  │
│  │ (Wasserstein,│  │ metrics.txt    │  │ (scraping toutes les 5s)    │  │
│  │  Jensen-Shan)│  └────────────────┘  └──────────────────────────────┘  │
│  └──────────────┘                                                        │
│  ┌──────────────┐  ┌────────────────┐                                    │
│  │ SRE Engine  │←│ Seuil 30%      │                                    │
│  │ (auto-       │  │ franchi ?      │                                    │
│  │  retrain)    │  └────────────────┘                                    │
│  └──────────────┘                                                        │
└───────────────────────────────────────────────────────────────────────────┘
        ▲
        │ Lit feature_matrix.parquet + shadow_log.csv
        │
┌───────────────────────────────────────────────────────────────────────────┐
│                    DATA PIPELINE (Médaillon)                              │
│                                                                           │
│  ┌────────────┐    ┌────────────────┐    ┌─────────────────────────┐     │
│  │  BRONZE    │ →  │    SILVER      │ →  │        GOLD             │     │
│  │ 4 CSVs     │    │ 4 Parquets     │    │ feature_matrix.parquet  │     │
│  │ 2.1M lignes│    │ Harmonisés     │    │ 946K lignes × 88 cols   │     │
│  │ generate_  │    │ harmonizer.py  │    │ build_features.py       │     │
│  │ synthetic  │    │ + contracts.py │    │ + calendar_utils.py     │     │
│  └────────────┘    └────────────────┘    └─────────────────────────┘     │
│                                                                           │
│  Orchestré par DVC (dvc.yaml) + Prefect (scripts/run_pipeline.py)        │
└───────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                       ML & SERVING                                        │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────────────────┐  │
│  │ train_       │→│ MLflow Server  │→│ FastAPI Serving (port 8000)  │  │
│  │ famille.py   │  │ (port 5001)    │  │ + Feast Redis (port 6379)   │  │
│  │ Famille A/B/C│  │ Registry MinIO │  │ + Shadow Logging Postgres   │  │
│  └──────────────┘  └────────────────┘  └──────────────────────────────┘  │
│                                                                           │
│  ┌──────────────┐  ┌────────────────┐                                    │
│  │ Apache       │  │ Streamlit      │                                    │
│  │ Superset     │  │ Dashboard      │                                    │
│  │ (port 8088)  │  │ (port 8501)    │                                    │
│  └──────────────┘  └────────────────┘                                    │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Stack Technique Complète

| Catégorie | Outil | Version | Rôle |
|---|---|---|---|
| **Langage** | `Python` | 3.10.12 | Runtime principal |
| **Package Manager** | `uv` | latest | Gestion des dépendances |
| **Base de données** | `PostgreSQL` | 17 | Data Warehouse + Metadata MLflow |
| **Object Storage** | `MinIO` | latest | Stockage S3 local des artefacts MLflow |
| **ML Tracking** | `MLflow` | 3.15.1 | Tracking, Registry, Model Serving |
| **Feature Store** | `Feast` | 0.47.0 | Offline (Postgres) + Online (Redis) |
| **Cache Online** | `Redis` | 7 | Feature Store temps réel |
| **Data Contracts** | `Pandera` | 0.32.1 | Validation de schéma strict |
| **Drift Detection** | `Evidently AI` | 0.7.23 | Jensen-Shannon, Wasserstein, PSI |
| **Orchestration** | `Prefect` | latest | Flows de drift, pipeline, et Control Plane |
| **Data Versioning** | `DVC` | 3.67.1 | Versioning des données brutes et harmonisées |
| **Serving API** | `FastAPI` | 0.141.1 | Inférence temps réel |
| **Monitoring** | `Prometheus` | latest | Scraping de métriques |
| **BI / Observabilité** | `Apache Superset` | latest | Exploration SQL du Data Warehouse |
| **Dashboard Agents** | `Streamlit` | latest | Visualisation du Control Plane |
| **ML Framework** | `scikit-learn` | 1.7.2 | Entraînement des modèles |
| **LLM Framework** | `instructor` + `litellm` | latest | Typage structuré des agents LLM |
| **Conteneurisation** | `Docker Compose` | 3.8 | Orchestration multi-services |
| **CI/CD** | `GitHub Actions` | v3 | Tests automatisés + build Docker |
| **Linting** | `pre-commit` | 4.6.1 | Hooks de qualité code |

**Fichier de déclaration** : [`pyproject.toml`](file:///Users/nolll/Documents/car_acc/pyproject.toml) (31 lignes, 26 dépendances)

---

## 3. Infrastructure Conteneurisée (Docker Compose)

**Fichier** : [`docker-compose.yml`](file:///Users/nolll/Documents/car_acc/docker-compose.yml) — 147 lignes

L'infrastructure locale est composée de **9 services** orchestrés par Docker Compose :

| Service | Image | Port | Rôle |
|---|---|---|---|
| `db` | `postgres:17` | `5432` | Data Warehouse principal + backend MLflow |
| `minio` | `minio/minio:latest` | `9000` (API) / `9001` (Console) | Object Storage S3 local |
| `minio-init` | `minio/mc:latest` | — | Création automatique du bucket `mlflow` |
| `mlflow` | `python:3.10-slim` | `5001→5000` | Serveur MLflow Tracking & Registry |
| `mlflow-serve` | `python:3.10-slim` | `5002` | Model Serving natif MLflow (Famille A) |
| `redis` | `redis:7` | `6379` | Online Feature Store (Feast) |
| `prometheus` | `prom/prometheus:latest` | `9090` | Collecte des métriques de drift et API |
| `pushgateway` | `prom/pushgateway:latest` | `9091` | Réception des métriques push (jobs batch) |
| `fastapi-serving` | Build local (`Dockerfile.api`) | `8000` | API d'inférence temps réel |
| `superset` | `apache/superset:latest` | `8088` | BI / Data Observability |

### Détails d'interconnexion

- **MLflow → Postgres** : `--backend-store-uri postgresql://mlops:mlops_password@db:5432/mlops_db`
- **MLflow → MinIO** : `--default-artifact-root s3://mlflow/` avec variables `AWS_ACCESS_KEY_ID=minioadmin`
- **FastAPI → Feast Redis** : Lookup en ligne des features pour l'inférence
- **Superset → Postgres** : Exploration SQL du Data Warehouse via [`datasources.yaml`](file:///Users/nolll/Documents/car_acc/superset_config/datasources.yaml)
- **Prometheus → FastAPI** : Scraping `/metrics` toutes les 5 secondes (cf. [`prometheus.yml`](file:///Users/nolll/Documents/car_acc/prometheus.yml))

### Fichiers associés

| Fichier | Lignes | Rôle |
|---|---|---|
| [`Dockerfile.api`](file:///Users/nolll/Documents/car_acc/Dockerfile.api) | 38 | Image Docker de production FastAPI |
| [`prometheus.yml`](file:///Users/nolll/Documents/car_acc/prometheus.yml) | 14 | Config scraping Prometheus |
| [`superset-init.sh`](file:///Users/nolll/Documents/car_acc/superset-init.sh) | 32 | Auto-provisioning Superset (admin, rôles, datasource) |
| [`superset_config/datasources.yaml`](file:///Users/nolll/Documents/car_acc/superset_config/datasources.yaml) | 9 | Connexion Postgres as-code |

---

## 4. Pipeline de Données — Architecture Médaillon

### 4.1 Couche Bronze — Génération Synthétique

**Fichier** : [`scripts/generate_synthetic_baac.py`](file:///Users/nolll/Documents/car_acc/scripts/generate_synthetic_baac.py) — 183 lignes

Ce script génère **300 000 accidents** répartis sur 6 années (2019-2024), produisant ~2,1 millions de lignes au total réparties dans 4 tables CSV :

| Table | Lignes approx. | Taille | Colonnes clés |
|---|---|---|---|
| `caracteristiques.csv` | 300 000 | 25.6 Mo | `Num_Acc`, `an`, `mois`, `jour`, `hrmn`, `lum`, `dep`, `lat`, `long` |
| `lieux.csv` | 300 000 | 17.5 Mo | `Num_Acc`, `catr`, `circ`, `surf`, `situ`, `vma` (post-2023) |
| `vehicules.csv` | ~660 000 | 23.8 Mo | `Num_Acc`, `id_vehicule`, `catv`, `choc`, `manv` |
| `usagers.csv` | ~1 150 000 | 49.8 Mo | `Num_Acc`, `id_vehicule`, `catu`, `grav`, `sexe`, `an_nais`, `trajet` |

**Fidélité aux anomalies BAAC réelles** :
- **`hrmn` (heures)** : Format entier `1446` en 2019-2020, **dates corrompues** `2023-08-29` (~30%) en 2021-2022, format `HH:MM` en 2023-2024
- **`dep` (départements)** : Codes métropolitains classiques + Corse (`2A`, `2B`) + DOM (`971`-`974`) à 10%
- **`secu` (sécurité)** : Colonne unique pré-2023, **scindée en 3 colonnes** (`secu1`, `secu2`, `secu3`) post-2023
- **`vma` (vitesse max)** : Colonne absente avant 2023, présente après
- **`grav` (gravité)** : Rupture sémantique post-2018 (redéfinition OMS de "blessé hospitalisé")
- **Shadow Log** : Génération d'un `shadow_log.csv` (5 000 lignes) avec **dérive intentionnelle** (vieillissement `an_nais` +5 ans, shift `trajet`) pour tester le monitoring

### 4.2 Couche Silver — Harmonisation Défensive

**Fichier** : [`src/data/harmonizer.py`](file:///Users/nolll/Documents/car_acc/src/data/harmonizer.py) — 283 lignes

La classe `BAACHarmonizer` exécute un pipeline de 6 étapes sur chacune des 4 tables :

| Étape | Méthode | Rôle |
|---|---|---|
| **1. Ingestion défensive** | `_step1_ingest()` | Lecture `dtype=str`, `encoding=latin-1`, détection auto du séparateur via `csv.Sniffer()`, normalisation des noms de colonnes en minuscules, injection de `source_year` |
| **2. Réconciliation de clés** | `_step2_reconcile_keys()` | Renommage `Accident_Id` → `Num_Acc`, zero-padding à 12 caractères, déduplication des lieux |
| **3. Anomalies structurelles** | `_step3_fix_anomalies()` | Correction multi-format de `hrmn` (entier→`HH:MM`, date→`NaN`+flag), split de `secu`, calcul de `is_metropole`, `is_post_2018_grav_definition`, `geo_level` |
| **4. Valeurs manquantes** | `_step4_unify_missing()` | Remplacement de `-1`, `N/A`, `NaN`, `(1)`, `""` par `pd.NA` |
| **5. Consolidation géo** | `_step5_consolidate_geo()` | Ajout de `territoire`, padding de `vma` à `NaN` pour les années pré-2023 |
| **6. Validation** | `_step6_validate()` | Validation Pandera, assertion `drop_rate < 5%`, export en Parquet |

**Sortie** : 4 fichiers Parquet dans `data/harmonized/` (~31 Mo total)

### 4.3 Data Contracts (Pandera)

**Fichier** : [`src/data/contracts.py`](file:///Users/nolll/Documents/car_acc/src/data/contracts.py) — 60 lignes

Quatre schémas `DataFrameModel` garantissent l'intégrité des données :

| Schéma | Contraintes clés |
|---|---|
| `BAACCaracteristiquesSchema` | `Num_Acc` unique & non-null, `an` ∈ [2005, 2026], `mois` ∈ [1, 12], `lum` ∈ {1-5}, `lat` ∈ [-90, 90] |
| `BAACLieuxSchema` | `Num_Acc` non-null, `catr` nullable, `surf` nullable |
| `BAACVehiculesSchema` | `Num_Acc` + `id_vehicule` non-null, `catv` nullable |
| `BAACUsagerSchema` | `usager_id` unique, `grav` ∈ {1,2,3,4}, `catu` ∈ {1,2,3}, `an_nais` ∈ [1900, 2026] |

Configuration : `strict=False`, `coerce=True` (souplesse pragmatique sur les colonnes non déclarées).

### 4.4 Couche Gold — Feature Engineering

**Fichier** : [`src/features/build_features.py`](file:///Users/nolll/Documents/car_acc/src/features/build_features.py) — 335 lignes

La classe `FeatureEngineer` fusionne les 4 tables au **grain Usager** (LEFT JOINs en cascade) puis calcule les features des 6 cas d'usage définis dans la Bible ML :

| Cas d'Usage | Features Générées | Méthode |
|---|---|---|
| **Base** | `age`, `age_bucket` (6 tranches), `is_motorise`, `is_deux_roues`, `is_lourd`, `hour`, `periode_jour`, `is_night`, `atm_simplifie` | `_build_age_features()`, `_build_vehicle_flags()`, `_build_time_features()`, `_build_weather_simple()` |
| **UC1 : Anticipation Temporelle** | `jour_semaine`, `is_weekend`, `is_ferie`, `is_vacances_scolaires` | `_build_temporal_features()` — utilise [`calendar_utils.py`](file:///Users/nolll/Documents/car_acc/src/features/calendar_utils.py) (86 lignes, computus grégorien) |
| **UC2 : Positionnement Urgences** | `creneau_2h`, `grav_max_accident`, `hrmn_valide` | `_build_positioning_features()` |
| **UC3 : Zones à Risque** | `nb_accidents_zone`, `taux_gravite_zone`, `granularite_fiable` | `_build_zone_risk_features()` |
| **UC4 : Aide Infra** | `risque_relatif_catr`, `vma_disponible` | `_build_infra_features()` |
| **UC5 : Aide T0 Urgence** | `lum_calculee`, `catr_derive` | `_build_t0_features()` |
| **UC6 : Alerte Météo** | `risque_historique_meteo` (Faible/Modéré/Élevé) | `_build_weather_alert_features()` |
| **Cible** | `grav_binary` : 1 si `grav` ∈ {2,3} (Grave), 0 si {1,4} (Léger) | `_build_target()` |
| **Feast** | `event_timestamp` (datetime) | `_add_feast_timestamp()` |

**Sortie** : [`data/features/feature_matrix.parquet`](file:///Users/nolll/Documents/car_acc/data/features/) — **946 224 lignes × 88 colonnes** (46.7 Mo)

### 4.5 Orchestration DVC

**Fichier** : [`dvc.yaml`](file:///Users/nolll/Documents/car_acc/dvc.yaml) — 27 lignes

```
generate_data ──→ harmonize
     │                  │
     ▼                  ▼
 data/raw/*.csv    data/harmonized/*.parquet
```

Deux stages déclaratifs avec lignage complet des dépendances. Le fichier [`dvc.lock`](file:///Users/nolll/Documents/car_acc/dvc.lock) (75 lignes) verrouille les hashes MD5 de chaque artefact pour garantir l'idempotence du cache.

---

## 5. Référentiels de Configuration

### `config/value_dictionaries.yaml` — 314 lignes
[`Voir le fichier`](file:///Users/nolll/Documents/car_acc/config/value_dictionaries.yaml)

Référentiel normatif ONISR complet pour **16 variables catégorielles** :
- `lum` (5 valeurs), `agg` (2), `int` (9), `atm` (9), `col` (7), `catr` (7), `circ` (4), `surf` (9), `situ` (8), `catv` (34 — dont EDPM ajoutés en 2019), `choc` (10), `manv` (27), `catu` (3), `grav` (4 — avec rupture sémantique 2018), `sexe` (2), `trajet` (7), `secu` (6 — avec rupture structurelle 2023)

Chaque entrée documente : `description`, `table`, `values`, `stable_since`, `known_breaks`, `missing_codes`.

### `config/column_lineage.yaml` — 120 lignes
[`Voir le fichier`](file:///Users/nolll/Documents/car_acc/config/column_lineage.yaml)

Matrice de lignage documentant la transformation de chaque colonne brute vers sa cible harmonisée :
- `num_acc` : 3 sources différentes (`Num_Acc` 2005-2021, `Accident_Id` 2022, `Num_Acc` 2023-2024)
- `hrmn` : 4 formats différents selon l'année
- `secu_split` : Colonne unique → 3 colonnes
- `is_metropole`, `territoire`, `geo_level`, `usager_id` : Colonnes dérivées

---

## 6. Usine d'Entraînement ML & Model Registry

**Fichier** : [`src/models/train_famille.py`](file:///Users/nolll/Documents/car_acc/src/models/train_famille.py) — 328 lignes

Trois familles de modèles sont entraînées sur la Feature Matrix Gold :

| Famille | Type | Modèle | Métriques | Registry |
|---|---|---|---|---|
| **A** | Classification binaire (gravité) | `RandomForestClassifier` | Accuracy ~70%, F1 ~73% | `BAAC_Model_Famille_A` v5 |
| **B** | Régression | `GradientBoostingRegressor` | MAE ~20.9 | `BAAC_Model_Famille_B` v5 |
| **C** | Hybride (Clustering + Prédiction) | Pipeline composite | Silhouette + F1 | `BAAC_Model_Famille_C` v6 |

**Workflow d'entraînement** :
1. Lecture de `feature_matrix.parquet`
2. Sélection des colonnes numériques/booléennes
3. Imputation (`SimpleImputer` median) + Scaling (`StandardScaler`)
4. `train_test_split` (80/20, `random_state=42`)
5. Logging MLflow (`mlflow.autolog()`) + enregistrement dans le Model Registry
6. Upload des poids vers le bucket MinIO (`s3://mlflow/`)

**Variables d'environnement requises** :
```bash
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadminpassword
MLFLOW_S3_ENDPOINT_URL=http://localhost:9000
MLFLOW_TRACKING_URI=http://localhost:5001
```

### Fichiers associés

| Fichier | Lignes | Rôle |
|---|---|---|
| [`src/models/train_famille_A.py`](file:///Users/nolll/Documents/car_acc/src/models/train_famille_A.py) | 111 | Entraînement standalone Famille A |
| [`src/models/sre_engine.py`](file:///Users/nolll/Documents/car_acc/src/models/sre_engine.py) | 99 | Boucle fermée SRE : surveille le PSI et déclenche le ré-entraînement automatique |
| [`src/models/drift_monitor.py`](file:///Users/nolll/Documents/car_acc/src/models/drift_monitor.py) | 84 | Calculateur PSI (Population Stability Index) entre distributions ref/prod |

---

## 7. Monitoring de Dérive (Drift)

**Fichier** : [`scripts/run_drift_analysis.py`](file:///Users/nolll/Documents/car_acc/scripts/run_drift_analysis.py) — 426 lignes

Ce flux Prefect compare la Feature Matrix Gold (référence) au Shadow Log de production :

**Étapes** :
1. Charger `feature_matrix.parquet` (946K lignes) comme données de référence
2. Charger `shadow_log.csv` (5K lignes) comme données de production
3. Aligner les features communes, forcer le cast `float64` (patch du bug Evidently `np.corrcoef`)
4. Exécuter `DataDriftPreset()` d'Evidently AI
5. Générer le rapport HTML interactif dans `reports/drift/`
6. Exporter les métriques au format Prometheus dans `prometheus_metrics.txt`
7. Si `drift_share > 30%` : déclencher le `SRE_Engine`

**Métriques exportées** :
```prometheus
# HELP mlops_baac_drift_share Proportion de features en dérive
mlops_baac_drift_share 0.4
# HELP mlops_baac_feature_drift_score Score de dérive par feature
mlops_baac_feature_drift_score{feature="an_nais"} 0.3337
mlops_baac_feature_drift_score{feature="trajet"} 0.4703
```

**Résultats observés** (Run du 02/10/2026) :
- **Drift Share** : 40% des features ont dérivé
- **`an_nais`** : Wasserstein = 0.3337 (vieillissement +5 ans détecté)
- **`trajet`** : Wasserstein = 0.4703 (shift de distribution détecté)

---

## 8. Couche Agentique — Agentic Control Plane

**Répertoire** : [`agentic-control-plane/`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/) — 35+ fichiers source

### 8.1 Architecture du Core

Le Control Plane suit une architecture **Hexagonale** (Ports & Adapters) :

```
                   ┌──────────────────────┐
                   │       CORE           │
                   │  (Zéro dépendance    │
                   │   externe)           │
                   │                      │
                   │  contracts.py        │
                   │  policy.py           │
                   │  evidence.py         │
                   │  state.py            │
                   │  idempotency.py      │
                   └──────────┬───────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                  ▼
    ┌───────────────┐ ┌──────────────┐  ┌──────────────┐
    │  ADAPTERS     │ │   RUNTIME    │  │ ENTRYPOINTS  │
    │               │ │              │  │              │
    │ baac/         │ │ orchestrator │  │ prefect_app  │
    │ mlflow/       │ │ specialist   │  │ demo.py      │
    │ infra/        │ │ remediation  │  └──────────────┘
    │ fake/         │ │ executor     │
    │ protocol.py   │ │ model_spec.  │
    └───────────────┘ │ infra_spec.  │
                      └──────────────┘
```

**Règle absolue** : Le module `agentic/core/` n'importe **jamais** un provider concret (Evidently, MLflow, PostgreSQL, GitHub, Prefect). Il ne manipule que des contrats Pydantic purs.

### 8.2 Les 7 Contrats Canoniques

**Fichier** : [`agentic/core/contracts.py`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/agentic/core/contracts.py) — 126 lignes

| # | Contrat | Champs Clés | Rôle |
|---|---|---|---|
| 1 | `Risk` | `id`, `severity` (1-5), `detectability`, `blast_radius`, `allowed_actions` | Définition statique d'un risque connu |
| 2 | `Signal` | `signal_id`, `value`, `threshold`, `source`, `dimensions` | Observation mesurée par un adaptateur. Propriété `breached` = `value > threshold` |
| 3 | `Diagnosis` | `risk_id`, `agent`, `confidence`, `findings[]` | Résultat d'analyse du Specialist. Chaque `Finding` a une `description` et un `evidence_ref` |
| 4 | `ActionProposal` | `type` (enum 8 valeurs), `risk_id`, `requested_by`, `reversible`, `blast_radius`, `parameters` | Plan d'action proposé par le RemediationAgent |
| 5 | `PolicyDecision` | `decision` (ALLOW/REQUIRE_APPROVAL/DENY), `matched_rule`, `reason_codes` | Verdict du PolicyEngine |
| 6 | `ExecutionResult` | `status`, `executor`, `result_ref`, `details` | Résultat de l'exécution de l'action |
| 7 | `Episode` | Agrège Signal + Diagnosis + ActionProposal + PolicyDecision + ExecutionResult + `state_trace` | Contrat d'évidence non-répudiable |

**Types d'action** (enum `ActionType`) :
`INVESTIGATE`, `CREATE_ISSUE`, `PROPOSE_RETRAIN`, `EXECUTE_RETRAIN`, `DEPLOY_STAGING`, `DEPLOY_PROD`, `ROLLBACK_PROD`, `DATABASE_WRITE`

### 8.3 Machine à États (State Machine)

**Fichier** : [`agentic/core/state.py`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/agentic/core/state.py) — 40 lignes

```
DETECTED → INVESTIGATING → DIAGNOSED → PLANNED → EXECUTING → RESOLVED
                                                          ↘ BLOCKED
                                                          ↘ WAITING_APPROVAL
```

Transitions valides définies explicitement. Toute transition non déclarée lève une `ValueError`.

### 8.4 Policy Engine (Gouvernance)

**Fichier** : [`agentic/core/policy.py`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/agentic/core/policy.py) — 67 lignes

Le `PolicyEngine` est une **fonction pure** (aucun LLM, aucun réseau) qui évalue chaque `ActionProposal` contre les règles YAML :

**[`governance/autonomy_policy.yaml`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/governance/autonomy_policy.yaml)** (21 lignes) :

| Action | Autonomie | Conditions |
|---|---|---|
| `investigate` | ✅ Autonome | — |
| `create_issue` | ✅ Autonome | `blast_radius_max: 2` |
| `propose_retrain` | ✅ Autonome | — |
| `execute_retrain` | 🔒 Approbation humaine | — |
| `deploy_staging` | 🔒 Approbation humaine | — |
| `deploy_prod` | 🔒 Approbation humaine | — |
| `rollback_prod` | 🔒 Approbation humaine | — |
| `database_write` | 🔒 Approbation humaine | — |

**[`governance/risk_register.yaml`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/governance/risk_register.yaml)** (11 lignes) :
Risque `DATA-042` ("Progressive data drift") — sévérité 5, détectabilité 5, blast_radius 2, actions autorisées : `investigate`, `create_issue`, `propose_retrain`.

### 8.5 Adaptateurs d'Observabilité

**Interface** : [`agentic/adapters/protocol.py`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/agentic/adapters/protocol.py) — 15 lignes (`typing.Protocol`)

| Adaptateur | Fichier | Lignes | Source de données | Signal produit |
|---|---|---|---|---|
| **BAAC** | [`baac/observability.py`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/agentic/adapters/baac/observability.py) | 106 | Parse `prometheus_metrics.txt` (format Prometheus text exposition) | `data_drift` : drift_share + top 5 features triées par score descendant |
| **MLflow** | [`mlflow/observability.py`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/agentic/adapters/mlflow/observability.py) | 75 | Requête `mlflow.search_runs()` sur `mlflow.db` SQLite | `model_f1_drop` : F1-score du dernier run Famille A vs seuil 0.85 |
| **Infra** | [`infra/observability.py`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/agentic/adapters/infra/observability.py) | 71 | `os.path.getmtime()` de `shadow_log.csv` + existence de `usagers.parquet` | `shadow_log_staleness` : âge en heures vs seuil 24h |
| **Fake** | [`fake/observability.py`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/agentic/adapters/fake/observability.py) | 29 | Valeur simulée hardcodée | `data_drift` : preuve de la portabilité du Core |

### 8.6 Spécialistes LLM (Agents)

Chaque spécialiste utilise `instructor.from_litellm()` pour contraindre la sortie LLM vers un modèle Pydantic strict :

| Agent | Fichier | Lignes | Input | Output |
|---|---|---|---|---|
| `DataSpecialist` | [`runtime/specialist.py`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/agentic/runtime/specialist.py) | 48 | `Signal` de dérive | `Diagnosis` avec `findings[]` et `confidence` |
| `ModelSpecialist` | [`runtime/model_specialist.py`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/agentic/runtime/model_specialist.py) | 48 | `Signal` de chute F1 | `Diagnosis` (concept drift, feature importance) |
| `InfraSpecialist` | [`runtime/infra_specialist.py`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/agentic/runtime/infra_specialist.py) | 49 | `Signal` de staleness | `Diagnosis` (défaillance système, DB) |
| `RemediationAgent` | [`runtime/remediation_agent.py`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/agentic/runtime/remediation_agent.py) | 46 | `Diagnosis` | `ActionProposal` (type, reversible, blast_radius, parameters) |

**Note** : En l'absence de clé API, le script [`demo_prefect_flow.py`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/scripts/demo_prefect_flow.py) (103 lignes) utilise `unittest.mock.patch` pour injecter des bouchons dynamiques qui consomment les vrais signaux Prometheus.

### 8.7 Outils Agentiques (Tools)

**Base abstraite** : [`tools/base.py`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/agentic/tools/base.py) — 20 lignes (validation Pydantic des arguments avant exécution)

| Outil | Fichier | Lignes | Fonction |
|---|---|---|---|
| `CheckDVCStatus` | [`tools/data.py`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/agentic/tools/data.py) | 25 | Vérifie le statut DVC d'un dataset |
| `ValidatePanderaSchema` | `tools/data.py` | — | Valide les schémas Pandera |
| `CreateGitHubIssue` | [`tools/github.py`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/agentic/tools/github.py) | 16 | Création d'issues GitHub |
| `CheckDockerContainers` | [`tools/infra.py`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/agentic/tools/infra.py) | 25 | Inspection des conteneurs Docker |
| `CheckPostgresHealth` | `tools/infra.py` | — | Santé de PostgreSQL |
| `GetModelMetadata` | [`tools/model.py`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/agentic/tools/model.py) | 15 | Métadonnées MLflow |
| `QueryPrometheus` | [`tools/observability.py`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/agentic/tools/observability.py) | 28 | Interrogation Prometheus |
| `GetEvidentlyReport` | `tools/observability.py` | — | Rapports Evidently AI |

### 8.8 Evidence Store & Idempotence

**Evidence Store** : [`agentic/core/evidence.py`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/agentic/core/evidence.py) — 44 lignes
- Stockage **append-only** de fichiers JSON
- Index `_index.json` pour la déduplication
- Numérotation automatique `EP-0001`, `EP-0002`, ...

**Idempotence** : [`agentic/core/idempotency.py`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/agentic/core/idempotency.py) — 9 lignes
- Clé de déduplication SHA-256 : `hash(risk_id + signal_source + environment + detection_window)`
- Si un épisode avec le même `dedup_key` existe déjà → skip

**Épisodes générés** :
- [`evidence/EP-0001.json`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/evidence/EP-0001.json) — drift_share=75%, Decision=ALLOW
- [`evidence/EP-0002.json`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/evidence/EP-0002.json) — drift_share=40%, Decision=ALLOW

### 8.9 Orchestrateur Prefect

**Fichier** : [`agentic/entrypoints/prefect_app.py`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/agentic/entrypoints/prefect_app.py) — 137 lignes

Le flow Prefect `agentic_control_plane_flow` orchestre le cycle complet :

```python
@flow(name="Agentic Control Plane")
def agentic_control_plane_flow(risk_id, detection_window):
    signal = get_signal(risk_id)          # Task 1: Lecture adaptateur
    episode = process_episode(signal)     # Task 2: Orchestrateur → Evidence
    return episode
```

**Routage dynamique** des adaptateurs selon le `signal_id` :
- `data_drift` → `BAACObservabilityAdapter`
- `model_f1_drop` → `MLflowObservabilityAdapter`
- `shadow_log_staleness` → `InfraObservabilityAdapter`

**Déploiement** : [`prefect.yaml`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/prefect.yaml) (31 lignes) — cron quotidien `0 8 * * *` + webhook à la demande.

### 8.10 Trust Ledger (Évaluation Shadow)

**Fichier** : [`agentic/evaluation/trust_ledger.py`](file:///Users/nolll/Documents/car_acc/agentic-control-plane/agentic/evaluation/trust_ledger.py) — 70 lignes

Évalue en mode shadow la précision des diagnostics par rapport aux injecteurs de chaos :
- Taux de diagnostic correct
- Faux négatifs
- Confiance moyenne

---

## 9. API de Serving (FastAPI)

**Fichier** : [`app/main.py`](file:///Users/nolll/Documents/car_acc/app/main.py) — 178 lignes

L'API FastAPI expose l'inférence temps réel :

| Endpoint | Méthode | Rôle |
|---|---|---|
| `/predict` | POST | Inférence avec lookup Feast Redis + Shadow Logging PostgreSQL |
| `/health` | GET | Healthcheck |
| `/metrics` | GET | Métriques Prometheus (latence, compteurs HTTP) |

**Flux d'inférence** :
1. Réception du payload (validé par [`baac_schema.py`](file:///Users/nolll/Documents/car_acc/app/domain/baac_schema.py), 35 lignes)
2. Lookup des features online dans Redis via Feast
3. Chargement du modèle MLflow en cache ([`model_loader.py`](file:///Users/nolll/Documents/car_acc/app/serving/model_loader.py), 30 lignes)
4. Prédiction + logging du résultat dans PostgreSQL (shadow log)
5. Détection de dérive en temps réel via Z-Score ([`infrastructure/drift_monitor.py`](file:///Users/nolll/Documents/car_acc/app/infrastructure/drift_monitor.py), 71 lignes)

### Architecture Domaine (DDD)

| Fichier | Lignes | Rôle |
|---|---|---|
| [`app/domain/entities.py`](file:///Users/nolll/Documents/car_acc/app/domain/entities.py) | 95 | Entités : Dataset, DatasetVersion, TrainingRun, ModelVersion, Deployment |
| [`app/domain/events.py`](file:///Users/nolll/Documents/car_acc/app/domain/events.py) | 45 | Événements DDD (EDA) |
| [`app/domain/executions/models.py`](file:///Users/nolll/Documents/car_acc/app/domain/executions/models.py) | 27 | Modèle SQLAlchemy des exécutions de pipeline |
| [`app/domain/executions/state/machine.py`](file:///Users/nolll/Documents/car_acc/app/domain/executions/state/machine.py) | 25 | FSM des transitions d'exécution |
| [`app/domain/observations/models.py`](file:///Users/nolll/Documents/car_acc/app/domain/observations/models.py) | 25 | Schémas Pydantic pour alertes de dégradation |
| [`app/domain/remediation/policy_engine.py`](file:///Users/nolll/Documents/car_acc/app/domain/remediation/policy_engine.py) | 57 | Policy Engine FastAPI avec cooldown anti-flapping |

### API Endpoints additionnels

| Fichier | Lignes | Rôle |
|---|---|---|
| [`app/api/datasets.py`](file:///Users/nolll/Documents/car_acc/app/api/datasets.py) | 80 | CRUD datasets |
| [`app/api/executions.py`](file:///Users/nolll/Documents/car_acc/app/api/executions.py) | 71 | Orchestration DAG |
| [`app/api/inference.py`](file:///Users/nolll/Documents/car_acc/app/api/inference.py) | 80 | Routeur d'inférence avancé |

### Workflows de Simulation

| Fichier | Lignes | Rôle |
|---|---|---|
| [`app/workflows/baac_simulation.py`](file:///Users/nolll/Documents/car_acc/app/workflows/baac_simulation.py) | 50 | Enregistrement dataset + validation invariants |
| [`app/workflows/baac_serving_simulation.py`](file:///Users/nolll/Documents/car_acc/app/workflows/baac_serving_simulation.py) | 47 | Trafic opérationnel multi-scénarios |
| [`app/workflows/baac_drift_simulation.py`](file:///Users/nolll/Documents/car_acc/app/workflows/baac_drift_simulation.py) | 39 | Injection de décalage Lidar extrême |
| [`app/workflows/baac_chaos_simulation.py`](file:///Users/nolll/Documents/car_acc/app/workflows/baac_chaos_simulation.py) | 46 | Chaos Engineering (pannes API, data corrompue) |
| [`app/workflows/baac_sre_simulation.py`](file:///Users/nolll/Documents/car_acc/app/workflows/baac_sre_simulation.py) | 51 | Charge + vérification métriques `/metrics` |
| [`app/workflows/baac_training_dag.py`](file:///Users/nolll/Documents/car_acc/app/workflows/baac_training_dag.py) | 65 | DAG d'entraînement bout-en-bout |

---

## 10. Feature Store (Feast)

**Répertoire** : [`feature_repo/`](file:///Users/nolll/Documents/car_acc/feature_repo/)

| Fichier | Lignes | Rôle |
|---|---|---|
| [`feature_store.yaml`](file:///Users/nolll/Documents/car_acc/feature_repo/feature_repo/feature_store.yaml) | 14 | Config Feast : offline=PostgreSQL, online=Redis |
| [`features.py`](file:///Users/nolll/Documents/car_acc/feature_repo/feature_repo/features.py) | 44 | Entité `usager` + `FeatureView` `usagers_features` (15 features déclarées) |
| [`test_workflow.py`](file:///Users/nolll/Documents/car_acc/feature_repo/feature_repo/test_workflow.py) | 131 | Démo apply/materialize/retrieval |

**Source offline** : Requête SQL `SELECT * FROM feature_matrix` sur PostgreSQL
**Store online** : Redis `localhost:6379` (TTL 3650 jours)

---

## 11. Data Warehouse (PostgreSQL + dbt)

**Chargement** : [`scripts/load_to_postgres.py`](file:///Users/nolll/Documents/car_acc/scripts/load_to_postgres.py) — 35 lignes
- Lecture des 4 Parquets harmonisés → `DROP TABLE CASCADE` → `to_sql()` dans `raw_*`

**Transformation dbt** : Le projet dbt (non détaillé ici) transforme les tables `raw_*` en modèles Silver/Gold exploitables par Superset.

**Scripts batch** :
| Fichier | Lignes | Rôle |
|---|---|---|
| [`scripts/batch_shap.py`](file:///Users/nolll/Documents/car_acc/scripts/batch_shap.py) | 76 | Explicabilité SHAP globale → table PostgreSQL pour Superset |
| [`scripts/batch_zones.py`](file:///Users/nolll/Documents/car_acc/scripts/batch_zones.py) | 58 | Agrégation géographique par département → cartographie |
| [`scripts/generate_calendar_seed.py`](file:///Users/nolll/Documents/car_acc/scripts/generate_calendar_seed.py) | 19 | Seed calendrier pour dbt |
| [`scripts/run_pipeline.py`](file:///Users/nolll/Documents/car_acc/scripts/run_pipeline.py) | 100 | Flow Prefect maître (DVC → Postgres → dbt → MLflow → SHAP) |

---

## 12. Observabilité & Dashboards

### Apache Superset — Data Observability
- **URL** : `http://localhost:8088`
- **Identifiants** : `admin` / `admin`
- **Connexion** : PostgreSQL `mlops_db` auto-provisionnée
- **Rôle** : Exploration SQL du Data Warehouse (qualité, complétude, orphelins)

### Streamlit — Control Plane Observability
- **Fichier** : [`app/dashboard.py`](file:///Users/nolll/Documents/car_acc/app/dashboard.py) — 85 lignes
- **URL** : `http://localhost:8501` (après `streamlit run app/dashboard.py`)
- **Rôle** : Lecture des évidences JSON du Control Plane, visualisation de la chaîne de pensée des agents

### Prometheus — Métriques Infrastructure
- **URL** : `http://localhost:9090`
- **Cibles** : FastAPI `/metrics` + Pushgateway `9091`

### MLflow UI — Model Registry
- **URL** : `http://localhost:5001`
- **Expériences** : Familles A, B, C avec historique des runs

---

## 13. Tests & CI/CD

### Tests

| Fichier | Lignes | Rôle |
|---|---|---|
| [`tests/test_data_contracts.py`](file:///Users/nolll/Documents/car_acc/tests/test_data_contracts.py) | 68 | Validation que Pandera intercepte les corruptions de données |
| [`tests/test_api_serving.py`](file:///Users/nolll/Documents/car_acc/tests/test_api_serving.py) | 59 | Tests d'intégration de l'API de serving avec mocks Feast/MLflow |

### CI/CD — GitHub Actions

**Fichier** : [`.github/workflows/mlops-ci.yml`](file:///Users/nolll/Documents/car_acc/.github/workflows/mlops-ci.yml) — 45 lignes

Pipeline en 2 jobs :
1. **`test-and-validate`** : `pytest` sur les contrats de données + l'API de serving
2. **`build-and-push`** (sur `main` uniquement) : Build de l'image Docker `Dockerfile.api`

---

## 14. Inventaire Exhaustif des Fichiers

### Racine (19 fichiers)

| # | Fichier | Lignes | Rôle |
|---|---|---|---|
| 1 | `pyproject.toml` | 31 | Métadonnées projet + 26 dépendances |
| 2 | `docker-compose.yml` | 147 | Stack 9 services |
| 3 | `Dockerfile.api` | 38 | Image Docker FastAPI |
| 4 | `prometheus.yml` | 14 | Config scraping Prometheus |
| 5 | `superset-init.sh` | 32 | Auto-provisioning Superset |
| 6 | `dvc.yaml` | 27 | DAG de données DVC |
| 7 | `dvc.lock` | 75 | Hashes MD5 des artefacts |
| 8 | `Makefile` | 78 | Commandes raccourcies |
| 9 | `simulate_drift.py` | 42 | Injection d'anomalies démographiques |
| 10 | `main.py` | 7 | Point d'entrée boilerplate |
| 11 | `ARCHITECTURE_MLOPS_GLOBALE.md` | — | Ce document |
| 12 | `README.md` | 10 | Accueil du dépôt |
| 13 | `.pre-commit-config.yaml` | 15 | Hooks git pre-commit |
| 14 | `.python-version` | 1 | `3.10.12` |
| 15 | `.gitignore` | 9 | Exclusions Git |
| 16 | `.dvcignore` | 7 | Exclusions DVC |
| 17 | `test_evidently_data.py` | 21 | Validation format Evidently |
| 18 | `test_shadow.py` | 20 | Test shadow logging |
| 19 | `test_tables.py` | 6 | Inspection tables Postgres |

### `src/` — Module Source (12 fichiers)

| # | Fichier | Lignes |
|---|---|---|
| 20 | `src/data/harmonizer.py` | 283 |
| 21 | `src/data/contracts.py` | 60 |
| 22 | `src/features/__init__.py` | 1 |
| 23 | `src/features/build_features.py` | 335 |
| 24 | `src/features/calendar_utils.py` | 86 |
| 25 | `src/models/__init__.py` | 1 |
| 26 | `src/models/train_famille.py` | 328 |
| 27 | `src/models/train_famille_A.py` | 111 |
| 28 | `src/models/sre_engine.py` | 99 |
| 29 | `src/models/drift_monitor.py` | 84 |
| 30 | `src/warehouse/__init__.py` | 1 |
| 31 | `src/warehouse/load_to_postgres.py` | 35 |

### `app/` — Application & Serving (24 fichiers)

| # | Fichier | Lignes |
|---|---|---|
| 32 | `app/main.py` | 178 |
| 33 | `app/dashboard.py` | 85 |
| 34 | `app/api/datasets.py` | 80 |
| 35 | `app/api/executions.py` | 71 |
| 36 | `app/api/inference.py` | 80 |
| 37 | `app/domain/baac_schema.py` | 35 |
| 38 | `app/domain/entities.py` | 95 |
| 39 | `app/domain/events.py` | 45 |
| 40 | `app/domain/executions/models.py` | 27 |
| 41 | `app/domain/executions/state/machine.py` | 25 |
| 42 | `app/domain/observations/models.py` | 25 |
| 43 | `app/domain/remediation/policy_engine.py` | 57 |
| 44 | `app/infrastructure/database.py` | 28 |
| 45 | `app/infrastructure/drift_monitor.py` | 71 |
| 46 | `app/infrastructure/mlflow_adapter.py` | 41 |
| 47 | `app/infrastructure/models.py` | 44 |
| 48 | `app/infrastructure/sre_engine.py` | 65 |
| 49 | `app/serving/model_loader.py` | 30 |
| 50-55 | `app/workflows/baac_*.py` (6 fichiers) | 46-65 |

### `scripts/` (7 fichiers)

| # | Fichier | Lignes |
|---|---|---|
| 56 | `scripts/run_drift_analysis.py` | 426 |
| 57 | `scripts/generate_synthetic_baac.py` | 183 |
| 58 | `scripts/load_to_postgres.py` | 35 |
| 59 | `scripts/batch_shap.py` | 76 |
| 60 | `scripts/batch_zones.py` | 58 |
| 61 | `scripts/generate_calendar_seed.py` | 19 |
| 62 | `scripts/run_pipeline.py` | 100 |

### `config/` (2 fichiers)

| # | Fichier | Lignes |
|---|---|---|
| 63 | `config/value_dictionaries.yaml` | 314 |
| 64 | `config/column_lineage.yaml` | 120 |

### `feature_repo/` (4 fichiers utiles)

| # | Fichier | Lignes |
|---|---|---|
| 65 | `feature_repo/feature_store.yaml` | 14 |
| 66 | `feature_repo/features.py` | 44 |
| 67 | `feature_repo/test_workflow.py` | 131 |
| 68 | `feature_repo/README.md` | 61 |

### `tests/` + CI/CD (3 fichiers)

| # | Fichier | Lignes |
|---|---|---|
| 69 | `tests/test_data_contracts.py` | 68 |
| 70 | `tests/test_api_serving.py` | 59 |
| 71 | `.github/workflows/mlops-ci.yml` | 45 |

### `agentic-control-plane/` (35+ fichiers)

| # | Fichier | Lignes |
|---|---|---|
| 72 | `demo.py` | 71 |
| 73 | `prefect.yaml` | 31 |
| 74 | `requirements.txt` | 8 |
| 75 | `governance/autonomy_policy.yaml` | 21 |
| 76 | `governance/risk_register.yaml` | 11 |
| 77 | `evidence/EP-0001.json` | 75 |
| 78 | `evidence/EP-0002.json` | 72 |
| 79 | `evidence/_index.json` | 3 |
| 80 | `scripts/demo_prefect_flow.py` | 103 |
| 81 | `agentic/core/contracts.py` | 126 |
| 82 | `agentic/core/policy.py` | 67 |
| 83 | `agentic/core/evidence.py` | 44 |
| 84 | `agentic/core/state.py` | 40 |
| 85 | `agentic/core/idempotency.py` | 9 |
| 86 | `agentic/adapters/protocol.py` | 15 |
| 87 | `agentic/adapters/baac/observability.py` | 106 |
| 88 | `agentic/adapters/mlflow/observability.py` | 75 |
| 89 | `agentic/adapters/infra/observability.py` | 71 |
| 90 | `agentic/adapters/fake/observability.py` | 29 |
| 91 | `agentic/runtime/orchestrator.py` | 138 |
| 92 | `agentic/runtime/specialist.py` | 48 |
| 93 | `agentic/runtime/model_specialist.py` | 48 |
| 94 | `agentic/runtime/infra_specialist.py` | 49 |
| 95 | `agentic/runtime/remediation_agent.py` | 46 |
| 96 | `agentic/runtime/executor.py` | 32 |
| 97 | `agentic/entrypoints/prefect_app.py` | 137 |
| 98 | `agentic/evaluation/trust_ledger.py` | 70 |
| 99 | `agentic/tools/base.py` | 20 |
| 100 | `agentic/tools/data.py` | 25 |
| 101 | `agentic/tools/github.py` | 16 |
| 102 | `agentic/tools/infra.py` | 25 |
| 103 | `agentic/tools/model.py` | 15 |
| 104 | `agentic/tools/observability.py` | 28 |

### Données & Rapports

| Chemin | Taille | Type |
|---|---|---|
| `data/raw/caracteristiques.csv` | 25.6 Mo | Bronze |
| `data/raw/lieux.csv` | 17.5 Mo | Bronze |
| `data/raw/usagers.csv` | 49.8 Mo | Bronze |
| `data/raw/vehicules.csv` | 23.8 Mo | Bronze |
| `data/harmonized/caracteristiques.parquet` | 9.5 Mo | Silver |
| `data/harmonized/lieux.parquet` | 4.2 Mo | Silver |
| `data/harmonized/usagers.parquet` | 13.0 Mo | Silver |
| `data/harmonized/vehicules.parquet` | 4.5 Mo | Silver |
| `data/features/feature_matrix.parquet` | 46.7 Mo | Gold |
| `data/production_logs/shadow_log.csv` | ~500 Ko | Production |
| `reports/drift/prometheus_metrics.txt` | ~1 Ko | Métriques |
| `reports/drift/drift_report_*.html` | ~2 Mo chacun | Rapports Evidently |

---

## 15. Commandes de Référence

```bash
# ══════════════════════════════════════════════════════
#  INFRASTRUCTURE
# ══════════════════════════════════════════════════════

# Démarrer toute la stack
docker compose up -d

# Vérifier les conteneurs
docker compose ps

# Logs Superset
docker compose logs -f superset

# ══════════════════════════════════════════════════════
#  PIPELINE DE DONNÉES
# ══════════════════════════════════════════════════════

# Générer 300K accidents synthétiques (Bronze)
.venv/bin/python scripts/generate_synthetic_baac.py

# Harmoniser (Silver) via DVC
dvc repro

# Construire la Feature Matrix (Gold)
PYTHONPATH=. .venv/bin/python src/features/build_features.py

# Charger dans PostgreSQL
.venv/bin/python scripts/load_to_postgres.py

# ══════════════════════════════════════════════════════
#  ENTRAÎNEMENT ML
# ══════════════════════════════════════════════════════

# Variables d'environnement MinIO
export AWS_ACCESS_KEY_ID=minioadmin
export AWS_SECRET_ACCESS_KEY=minioadminpassword
export MLFLOW_S3_ENDPOINT_URL=http://localhost:9000
export MLFLOW_TRACKING_URI=http://localhost:5001

# Entraîner les 3 familles
PYTHONPATH=. .venv/bin/python src/models/train_famille.py

# ══════════════════════════════════════════════════════
#  MONITORING & DRIFT
# ══════════════════════════════════════════════════════

# Lancer l'analyse de dérive (Evidently)
PYTHONPATH=. .venv/bin/python scripts/run_drift_analysis.py

# ══════════════════════════════════════════════════════
#  CONTROL PLANE AGENTIQUE
# ══════════════════════════════════════════════════════

# Démo complète (signaux réels + LLM mockés)
cd agentic-control-plane && PYTHONPATH=. ../.venv/bin/python scripts/demo_prefect_flow.py

# ══════════════════════════════════════════════════════
#  DASHBOARDS
# ══════════════════════════════════════════════════════

# Superset (BI)          → http://localhost:8088 (admin/admin)
# MLflow UI              → http://localhost:5001
# Prometheus             → http://localhost:9090
# MinIO Console          → http://localhost:9001 (minioadmin/minioadminpassword)

# Dashboard Streamlit (Control Plane)
.venv/bin/streamlit run app/dashboard.py
# → http://localhost:8501

# ══════════════════════════════════════════════════════
#  TESTS
# ══════════════════════════════════════════════════════

# Tests de contrats de données
pytest tests/test_data_contracts.py -v

# Tests de l'API de serving
pytest tests/test_api_serving.py -v
```
