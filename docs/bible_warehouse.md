# 📖 Bible des Méga Copier-Coller Warehouse

> [!IMPORTANT]
> **Règles de ce document :**
> 1. **Chronologique** — Chaque partie est ajoutée dans l'ordre de réception.
> 2. **Non-destructif** — Aucune idée n'est supprimée. Si une idée devient obsolète ou évolue, elle est signalée avec un bandeau `[⚠️ ÉVOLUTION]` ou `[❌ OBSOLÈTE]` suivi de l'explication et du renvoi vers la nouvelle version.
> 3. **Bien structuré** — Organisé en 3 zones par partie pour éviter la "bouillie".
>
> Dernière mise à jour : 2026-06-25 — Partie 22/30 reçue.

---

## 🔭 Prisme MLOps — Cadre permanent de lecture

> [!CAUTION]
> **Ce projet est un projet MLOps.** Le travail Data Warehouse / Data Engineering
> **fait partie intégrante du projet** — c'est le socle concret de la Phase 1.
> Le prisme MLOps ne dit pas "on ignore le DW". Il dit :
> *"On construit le DW de la bonne façon, pour qu'il serve le ML en production."*
>
> La différence avec un projet DW "classique" : tout ce qu'on construit doit être
> **automatisé, reproductible, versionné et testable** — pas un one-shot dans un notebook.

### Cadre du projet

| Élément | Valeur |
|---------|--------|
| **Objectif** | MLOps Roadmap — Prédiction de la gravité des accidents routiers |
| **Données** | BAAC (data.gouv.fr) 2005-2024, ~100 fichiers CSV |
| **Rôle principal** | MLOps Engineer (qui porte aussi la casquette Data Engineer en Phase 1) |
| **Livrables** | Pipeline automatisé, API d'inférence, monitoring, CI/CD |

### Phases de la roadmap

| Phase | Contenu | Date limite | Lien avec le DW |
|-------|---------|-------------|-----------------|
| **Phase 1** | Fondations & Conteneurisation | 15/06 | **C'est ici qu'on construit le pipeline de données (ETL, harmonisation, validation)** |
| **Phase 2** | MLflow, versioning, microservices | 29/06 | Versioning des données et du schéma (DVC) |
| **Phase 3** | Orchestration, CI/CD, déploiement | 27/07 | Orchestration du pipeline (Airflow), dashboards de monitoring |
| **Phase 4** | Monitoring, drift, observabilité | Post-livraison | KPI en production, détection de drift sur les données |

### Les 6 use cases métier retenus

1. Aide aux urgences (classification gravité)
2. Scoring des zones à risque
3. Anticipation temporelle
4. Aide à l'infrastructure
5. ~~Alerte météo~~ *(rejeté — dépendance externe)*
6. Positionnement des secours

### Règle de lecture

Pour chaque concept DW rencontré dans les copier-coller, je pose systématiquement **4 questions** :

1. **Quelle brique MLOps cela alimente-t-il ?** (Pipeline d'ingestion ? Feature engineering ? Monitoring ?)
2. **Est-ce un livrable du projet ou un sous-produit ?** (Le DW alimente le ML, il n'est pas une fin en soi)
3. **Quel est le coût d'opportunité ?** (Prioriser ce qui débloque le ML en premier)
4. **Comment je le construis pour que ce soit automatisable et reproductible ?** (Pas de one-shot : tout doit être scriptable, testable, rejouable)

### Mapping vivant : Concept DW → Brique MLOps → Réalisation

*Ce tableau grandit à chaque partie reçue. Chaque ligne est un travail concret à réaliser.*

| Concept DW | Brique MLOps | Phase | Priorité | À réaliser concrètement |
|------------|-------------|-------|----------|------------------------|
| ETL (Extract-Transform-Load) | `harmonizer.py` — Pipeline d'ingestion | Phase 1 | 🔴 Critique | Script Python automatisé, idempotent, testé |
| Schéma en étoile (Star Schema) | Sous-produit du pipeline → dashboards monitoring | Phase 3 | 🟡 Utile | Script SQL/Python qui génère les tables étoile à partir des Parquet harmonisés |
| FACT_ACCIDENT (grain Accident) | Table agrégée pour KPI et monitoring de drift | Phase 4 | 🟡 Utile | Vue agrégée calculée par le pipeline, loggée dans MLflow |
| DIM_DATE | Feature engineering temporel | Phase 1 | 🔴 Critique | Colonnes `hour_sin`, `day_of_week`, `is_weekend`, `month` dans le feature store |
| DIM_LIEU | Feature engineering géographique | Phase 1 | 🔴 Critique | Colonnes `dep`, `lat/long`, `agg`, `territoire` dans le feature store |
| DIM_VEHICULE | Features véhicule | Phase 1 | 🔴 Critique | Colonnes `catv`, `motor` dans la table ML |
| DIM_USAGER | Table ML à grain "Usager" (cible `grav`) | Phase 1 | 🔴 Critique | Table dénormalisée principale pour l'entraînement |
| Décodage variables codées | `value_dictionaries.yaml` | Phase 1 | 🔴 Critique | Fichier YAML + script de validation |
| KPI (taux mortalité, nb_tués) | Métriques de monitoring en production | Phase 4 | 🟡 Utile | Dashboard Grafana/Metabase connecté aux métriques du pipeline |
| PostgreSQL | Base de stockage du DW + feature store | Phase 1-3 | 🟡 Utile | Instance PostgreSQL (Docker), schéma créé par migration |
| Power BI / Tableau | Dashboard de monitoring (pas de reporting BI pur) | Phase 3 | 🟢 Optionnel | Alternative légère : Metabase ou Grafana en Docker |
| Airflow | Orchestrateur du pipeline ML complet | Phase 3 | 🟡 Utile | DAG Airflow : ingestion → harmonisation → entraînement → déploiement |
| Modèle conceptuel (MCD) | Documentation du pipeline (Model Card) | Phase 1 | 🔴 Critique | Section dans `docs/model_card.md` |
| Table de Télémétrie | Collecte des prédictions pour le `DriftMonitor` | Phase 8 | 🔴 Critique | Table PostgreSQL (Staging) stockant requêtes T0 et labels réels T1 pour détecter la dérive et alerter le `PolicyEngine` |


---

## Table des matières

- [Partie 1/20 — Modèle relationnel BAAC & Schéma en étoile](#partie-120--modèle-relationnel-baac--schéma-en-étoile)
- [Partie 2/20 — Architecture Data Warehouse & ETL](#partie-220--architecture-data-warehouse--etl)
- [Partie 3/20 — Dictionnaire des variables codées BAAC](#partie-320--dictionnaire-des-variables-codées-baac)
- [Partie 4/20 — Jointures, Duplication & Agrégation](#partie-420--jointures-duplication--agrégation)
- [Partie 5/20 — Pourquoi les jointures & Schéma enrichi](#partie-520--pourquoi-les-jointures--schéma-enrichi)
- [Partie 6/20 — Conception avancée DW (Niveau Entreprise)](#partie-620--conception-avancée-dw-niveau-entreprise)
- [Partie 7/20 — Modélisation MCD & UML (Approche Hybride)](#partie-720--modélisation-mcd--uml-approche-hybride)
- [Partie 8/20 — Conception Data Warehouse (PostgreSQL)](#partie-820--conception-data-warehouse-postgresql)
- [Partie 9/20 — Script ETL Pandas Monolithique](#partie-920--script-etl-pandas-monolithique)
- [Partie 10/20 — Architecture ETL Incrémental (Airflow)](#partie-1020--architecture-etl-incrémental-airflow)
- [Partie 11/20 — Data Quality Checks & Great Expectations](#partie-1120--data-quality-checks--great-expectations)
- [Partie 12/20 — Dockerisation Airflow & PostgreSQL](#partie-1220--dockerisation-airflow--postgresql)
- [Partie 13/30 — Couche de Transformation dbt (Analytics as Code)](#partie-1330--couche-de-transformation-dbt-analytics-as-code)
- [Partie 14/30 — Implémentation Great Expectations](#partie-1430--implémentation-great-expectations)
- [Partie 15/30 — Over-engineering : Airflow, Redis & Celery](#partie-1530--over-engineering--airflow-redis--celery)
- [Partie 16/30 — Data Observability (Apache Superset)](#partie-1630--data-observability-apache-superset)
- [Partie 17/30 — Le mirage du Lakehouse (Iceberg & Trino)](#partie-1730--le-mirage-du-lakehouse-iceberg--trino)
- [Partie 18/30 — Le Grand Récapitulatif et la Simulation Streaming](#partie-1830--le-grand-récapitulatif-et-la-simulation-streaming)
- [Partie 19/30 — La Défense du Cas d'Usage (Label Leakage & Runtime)](#partie-1930--la-défense-du-cas-dusage-label-leakage--runtime)
- [Partie 20/30 — L'Illusion de la Validation Industrielle (Hype-Driven Development)](#partie-2030--lillusion-de-la-validation-industrielle-hype-driven-development)
- [Partie 21/30 — La Fuite en Avant Technologique (L'Hétérogénéité des Données)](#partie-2130--la-fuite-en-avant-technologique-lhétérogénéité-des-données)
- [Partie 22/30 — L'Architecture Medallion et les Règles de Nettoyage](#partie-2230--larchitecture-medallion-et-les-règles-de-nettoyage)
- [Partie 23/20 — *(à venir)*](#partie-2320--à-venir)
- [📥 Backlog des recommandations non suivies](#-backlog-des-recommandations-non-suivies)
- [Journal d'évolution des idées](#journal-dévolution-des-idées)

---

# Partie 1/20 — Modèle relationnel BAAC & Schéma en étoile

**Date de réception :** 2026-06-25 09:37

---

## Zone A — Contenu brut archivé

*Ce que le LLM a dit, retranscrit fidèlement.*

### A1. Modèle relationnel BAAC

Les données BAAC sont organisées selon un modèle relationnel où **un accident est l'entité centrale**. Les autres tables décrivent le lieu, les véhicules impliqués et les usagers concernés.

```
                 +------------------+
                 |     CARACT       |
                 |------------------|
                 | Num_Acc (PK)     |
                 | Date, Heure      |
                 | Météo            |
                 | Luminosité       |
                 | Coordonnées      |
                 +--------+---------+
                          |
                          | 1:N
                          |
                 +--------v---------+
                 |      LIEUX       |
                 |------------------|
                 | Num_Acc (FK)     |
                 | Route            |
                 | Intersection     |
                 | Surface          |
                 | Vitesse max      |
                 +------------------+
                          |
                          | 1:N
                          |
                 +--------v---------+
                 |    VEHICULES     |
                 |------------------|
                 | id_vehicule (PK) |
                 | Num_Acc (FK)     |
                 | Catégorie        |
                 | Choc             |
                 | Manœuvre         |
                 +--------+---------+
                          |
                          | 1:N
                          |
                 +--------v---------+
                 |     USAGERS      |
                 |------------------|
                 | id_usager (PK)   |
                 | id_vehicule (FK) |
                 | Num_Acc (FK)     |
                 | Gravité          |
                 | Sexe             |
                 | Année naissance  |
                 +------------------+
```

### A2. Clés et relations

| Table | Clé primaire | Clé(s) étrangère(s) | Relation |
|-------|-------------|---------------------|----------|
| CARACT | `Num_Acc` | — | Table centrale |
| LIEUX | Pas de PK simple (`Num_Acc` + `voie`) | `Num_Acc` → CARACT | 1 accident → N lieux |
| VEHICULES | `id_vehicule` | `Num_Acc` → CARACT | 1 accident → N véhicules |
| USAGERS | `id_usager` | `Num_Acc` → CARACT, `id_vehicule` → VEHICULES | 1 véhicule → N usagers |

### A3. Cardinalités illustrées

**Accident → Lieux (1:N)** — Exemple : intersection de 2 rues
```
202400000002
 ├─ HOTEL DIEU (RUE DE L')
 └─ POTERNE (RUE)
```

**Accident → Véhicules (1:N)** — Exemple : 4 véhicules impliqués
```
202400000005
 ├─ A01
 ├─ B01
 ├─ C01
 └─ D01
```

**Véhicule → Usagers (1:N)** — Exemple : conducteur + passager
```
Vehicule A01
 ├─ Conducteur (id_usager: 203851175)
 └─ Passager   (id_usager: 203851176)
```

### A4. Jointures Pandas

```python
# Jointure complète
df_final = (
    caract
    .merge(lieux, on="Num_Acc", how="left")
    .merge(vehicules, on="Num_Acc", how="left")
    .merge(
        usagers,
        on=["Num_Acc", "id_vehicule"],
        how="left"
    )
)
```

### A5. Table vehicules-immatricules (hors schéma standard)

```
Id_accident | Catégorie véhicule | Age véhicule
416873      | Moto lourde        | 16
```

> [!WARNING]
> Cette table utilise `Id_accident` (pas `Num_Acc`) et un système d'identifiants différent.
> Nécessite une table de correspondance (à chercher dans la documentation officielle ONISR).

### A6. Schéma en étoile proposé (Data Warehouse / BI)

```
                 DIM_DATE
                      |
                      |
DIM_LIEU ---- FACT_ACCIDENT ---- DIM_VEHICULE
                      |
                      |
                 DIM_USAGER
```

**Table de faits :** Accident, Nombre de véhicules, Nombre de victimes, Nombre de blessés, Nombre de tués.

**Dimensions :** Date, Lieu, Véhicule, Usager.

---

## Zone B — Analyse et idées générées

*Observations originales, problèmes détectés, compléments.*

### B1. 🔴 PROBLÈME CRITIQUE — Le piège de granularité des jointures 1:N

**Identifié le :** 2026-06-25

**Le problème :** La jointure complète (A4) provoque une **explosion combinatoire** à cause des relations 1:N en cascade :

```
1 accident × 2 lieux × 4 véhicules × 6 usagers = 48 lignes
```

pour un seul accident réel. Conséquences :
- Le modèle ML s'entraîne sur 48 lignes quasi-identiques → **biais d'apprentissage**
- Les métriques sont faussées (accuracy gonflée artificiellement)
- **Data leakage** dans le train/test split (le même accident fuit entre les deux)

**La décision à prendre :** Choisir le grain de la table ML finale.

| Grain | 1 ligne = | Use cases adaptés | Jointure |
|-------|-----------|-------------------|----------|
| Accident | 1 accident | Anticipation temporelle, Zones à risque | `caract` + agrégations (`nb_vehicules`, `nb_tués`, etc.) |
| Usager | 1 personne | Aide aux urgences (gravité par personne) | Jointure complète mais split par `Num_Acc` (pas par ligne) |
| Véhicule | 1 véhicule | Analyse du parc roulant | Jointure intermédiaire |

> [!IMPORTANT]
> **Ce choix conditionne toute l'architecture du pipeline.** Il doit être documenté dans le Model Card et implémenté dans le `harmonizer.py` comme paramètre configurable (pas codé en dur).

### B2. 🟡 OBSERVATION — Le schéma en étoile vs la table plate ML

Le LLM propose un schéma en étoile (A6) classique pour le BI. C'est pertinent pour des dashboards, mais pour le ML, on a généralement besoin d'une **table dénormalisée (plate)**. Les deux approches ne sont pas incompatibles mais servent des objectifs différents :

| Approche | Objectif | Outil cible |
|----------|---------|-------------|
| Schéma en étoile | Dashboards, KPI, reporting | Metabase, Superset, Power BI |
| Table plate dénormalisée | Entraînement ML | Pandas, Scikit-learn, XGBoost |

**Idée :** Le pipeline pourrait produire **les deux sorties** à partir de la même source harmonisée — une pour le BI (Phase 3) et une pour le ML (Phase 1).

### B3. 🟡 OBSERVATION — La table LIEUX n'a pas de vraie clé primaire

Le LLM note que LIEUX n'a "pas de clé primaire simple" et suggère `Num_Acc + voie`. C'est un problème pour :
- La validation des Data Contracts (on ne peut pas vérifier l'unicité)
- Le comptage de lignes (un accident à une intersection comptera 2× dans LIEUX)

**Action pour le pipeline :** Décider si on garde toutes les lignes de LIEUX ou si on agrège (ex : ne garder que la première voie, ou concaténer les voies en une seule colonne `voies_concat`).

### B4. 🟡 OBSERVATION — La table vehicules-immatricules est un "orphelin relationnel"

La table `vehicules-immatricules-baac` utilise `Id_accident` au lieu de `Num_Acc`. Aucune table de correspondance n'a été identifiée. Pour l'instant :
- **Statut :** Inutilisable en jointure avec les 4 tables BAAC principales
- **Action requise :** Chercher dans la documentation ONISR si une correspondance existe
- **Plan B :** Ignorer cette table pour la Phase 1 et la traiter comme un enrichissement optionnel en Phase 2

---

## Zone C — Statut des idées (Partie 1/20)

| ID | Idée | Statut | Notes |
|----|------|--------|-------|
| B1 | Piège de granularité des jointures | 🟢 Active | Décision à prendre avant le build |
| B2 | Double sortie (étoile + plate) | 🟢 Active | À confirmer avec les parties suivantes |
| B3 | Absence de PK dans LIEUX | 🟢 Active | Stratégie d'agrégation à définir |
| B4 | Table vehicules-immatricules orpheline | 🟢 Active | En attente de documentation ONISR |

---

# Partie 2/20 — Architecture Data Warehouse & ETL

**Date de réception :** 2026-06-25 09:47

---

## Zone A — Contenu brut archivé

*Ce que le LLM a dit, retranscrit fidèlement.*

### A1. Objectif du Data Warehouse BAAC

Passer des fichiers opérationnels (CSV bruts) à un entrepôt de données structuré pour l'analyse, permettant de répondre rapidement à des questions métier :

| Question métier | Capacité requise |
|----------------|------------------|
| Combien d'accidents mortels par département ? | Temps de réponse très rapide |
| Quels profils d'usagers sont les plus touchés ? | Analyses multidimensionnelles |
| Quels sont les axes routiers les plus accidentogènes ? | Tableaux de bord et cartographie |

### A2. Architecture ETL / ELT

**Extraction :** Lecture des CSV (`pd.read_csv`)

**Transformation :**
- Nettoyage des valeurs manquantes
- Conversion des dates
- Décodage des variables codées :
  - `grav = 1` → Indemne
  - `grav = 2` → Tué
  - `grav = 3` → Blessé hospitalisé
  - `grav = 4` → Blessé léger
- Calcul d'indicateurs

**Chargement :** Insertion dans le Data Warehouse (PostgreSQL, SQL Server, Snowflake, BigQuery, Oracle)

### A3. Schéma en étoile détaillé

```
                    DIM_DATE
                        |
DIM_LIEU ---- FACT_ACCIDENT ---- DIM_VEHICULE
                        |
                   DIM_USAGER
```

#### FACT_ACCIDENT

| Colonne | Exemple |
|---------|---------|
| `id_accident` | 202400000001 |
| `nb_vehicules` | 2 |
| `nb_usagers` | 3 |
| `nb_tues` | 1 |
| `nb_blesses` | 2 |

#### DIM_DATE

| Colonne | Exemple |
|---------|---------|
| `date_key` | 20240325 |
| `date` | 25/03/2024 |
| `mois` | Mars |
| `année` | 2024 |

#### DIM_LIEU

À partir de `caract` + `lieux` : `lieu_key`, `département`, `commune`, `latitude`, `longitude`, `vitesse_max`

#### DIM_VEHICULE

À partir de `vehicules` : `vehicule_key`, `catégorie`, `manœuvre`, `type_choc`

#### DIM_USAGER

À partir de `usagers` : `usager_key`, `sexe`, `âge`, `gravité`, `catégorie`

### A4. KPI définis

| KPI | Formule |
|-----|---------|
| Nombre d'accidents | `COUNT(*)` |
| Nombre de tués | `SUM(nb_tues)` |
| Nombre de blessés | `SUM(nb_blesses)` |
| Taux de mortalité | `tués / accidents` |
| Nombre moyen de véhicules | `AVG(nb_vehicules)` |

### A5. Questions métier catégorisées

**Sécurité routière :** Quels départements ont le plus d'accidents/décès ? Quels horaires sont les plus dangereux ?

**Analyse géographique :** Carte des accidents, points noirs routiers, répartition urbaine/rurale.

**Analyse des victimes :** Répartition par âge, par sexe, gravité selon le mode de transport.

**Analyse des véhicules :** Motos et accidents graves, impact de l'âge du véhicule.

### A6. Stack technique proposée

| Couche | Outils |
|--------|--------|
| Stockage | PostgreSQL, SQL Server |
| ETL | Python (Pandas), Airflow, Talend, dbt |
| Visualisation | Power BI, Tableau, Looker Studio |

### A7. Exemple de sujet de mémoire

> *"Conception et réalisation d'un Data Warehouse pour l'analyse des accidents corporels de la circulation en France (2022-2024)"*
>
> Livrables : Modèle conceptuel (MCD), Schéma en étoile, Processus ETL Python, Base PostgreSQL, Tableau de bord Power BI, Analyse des facteurs de gravité.

---

## Zone B — Analyse et idées générées

### B5. 🔴 CONFIRMATION — Le grain FACT_ACCIDENT confirme et précise B1

**Identifié le :** 2026-06-25

**Lien avec B1 (Partie 1/20) :** La Partie 1 posait la question du grain. La Partie 2 y répond implicitement : **FACT_ACCIDENT a pour grain 1 ligne = 1 accident**, avec des mesures agrégées (`nb_tues`, `nb_blesses`, `nb_vehicules`).

Cela signifie que le LLM a choisi le grain "Accident" pour le Data Warehouse. **Mais attention** : ce grain n'est valide que pour le BI/reporting. Pour le ML (use case "Aide aux urgences" = prédire la gravité **par usager**), il faudra une table à grain "Usager" en parallèle.

> [!IMPORTANT]
> **[⚠️ ÉVOLUTION de B1]** — L'idée B1 (Partie 1) reste active mais est maintenant **précisée** : le grain "Accident" est confirmé pour le DW, mais le grain "Usager" reste nécessaire pour le ML. Les deux doivent coexister.

### B6. 🟡 OBSERVATION — Le décodage des variables est le pont vers `value_dictionaries.yaml`

La Partie 2 mentionne le décodage de `grav` (1→Indemne, 2→Tué, etc.) dans l'ETL. C'est exactement ce que le document [data_inventory_strategy.md](file:///Users/nolll/.gemini/antigravity/brain/10b271a9-5646-4286-b482-9f27ac791062/data_inventory_strategy.md) propose sous le nom `value_dictionaries.yaml` (section 2.2).

**Convergence :** Le décodage ETL du DW et le dictionnaire de valeurs du pipeline ML sont le **même artefact**. Ne pas les coder deux fois.

### B7. 🟡 OBSERVATION — Le KPI "Taux de mortalité" est trompeur sans normalisation

Le KPI `tués / accidents` est un classique du reporting, mais il souffre du **biais d'exposition** déjà identifié dans notre analyse des 6 use cases :
- Un département avec beaucoup de trafic aura mécaniquement plus d'accidents mais pas forcément un taux de mortalité plus élevé.
- Sans données de trafic (absentes du BAAC), ce KPI est utile pour le reporting interne mais **ne doit pas être utilisé pour comparer des départements** entre eux.

**Action :** Documenter cette limite dans le dashboard et dans le Model Card.

### B8. 🔴 PROBLÈME — Tension architecturale DW classique vs pipeline MLOps

**Identifié le :** 2026-06-25

La Partie 2 décrit un projet Data Warehouse "classique" (PostgreSQL + Power BI). Le projet réel est un projet **MLOps**. La question stratégique :

| Approche | Avantages | Risques |
|----------|-----------|--------|
| DW séparé (PostgreSQL + dashboards) | Livrable BI autonome, impressionne les évaluateurs | Double travail, maintenance de 2 systèmes |
| DW intégré au pipeline MLOps | Un seul pipeline, cohérence des données | Plus complexe à concevoir |
| DW comme sous-produit du pipeline | Le pipeline ML produit aussi les tables étoile | Meilleur compromis effort/valeur |

**Recommandation :** Option 3 — Le `harmonizer.py` produit les 4 tables unifiées en Parquet. Un script secondaire les transforme en schéma étoile pour PostgreSQL. Le pipeline ML et le DW partagent la même source de vérité.

> [!IMPORTANT]
> **[⚠️ ÉVOLUTION de B2]** — L'idée B2 (Partie 1, "double sortie étoile + plate") est maintenant **renforcée et précisée** par B8 : la recommandation est l'Option 3 (DW comme sous-produit du pipeline ML).

---

## Zone C — Statut des idées (Partie 2/20)

| ID | Idée | Statut | Notes |
|----|------|--------|-------|
| B5 | Grain FACT_ACCIDENT = Accident | 🟢 Active | Confirme B1, grain Usager toujours nécessaire pour ML |
| B6 | Décodage ETL = value_dictionaries.yaml | 🟢 Active | Ne pas dupliquer l'artefact |
| B7 | KPI taux de mortalité trompeur | 🟢 Active | Biais d'exposition à documenter |
| B8 | Tension DW classique vs MLOps | 🟢 Active | Option 3 recommandée (DW = sous-produit) |

---

# Partie 3/20 — Dictionnaire des variables codées BAAC

**Date de réception :** 2026-06-25 09:59

---

## Zone A — Contenu brut archivé

### A1. Variables de `caract`

#### `lum` — Conditions d'éclairage
| Code | Signification |
|------|---------------|
| 1 | Plein jour |
| 2 | Crépuscule ou aube |
| 3 | Nuit sans éclairage public |
| 4 | Nuit avec éclairage public non allumé |
| 5 | Nuit avec éclairage public allumé |

#### `agg` — Localisation
| Code | Signification |
|------|---------------|
| 1 | Hors agglomération |
| 2 | En agglomération |

#### `int` — Type d'intersection
| Code | Signification |
|------|---------------|
| 1 | Hors intersection |
| 2 | Intersection en X |
| 3 | Intersection en T |
| 4 | Intersection en Y |
| 5 | Intersection à plus de 4 branches |
| 6 | Giratoire |
| 7 | Place |
| 8 | Passage à niveau |
| 9 | Autre intersection |

#### `atm` — Conditions atmosphériques
| Code | Signification |
|------|---------------|
| 1 | Normales |
| 2 | Pluie légère |
| 3 | Pluie forte |
| 4 | Neige / grêle |
| 5 | Brouillard / fumée |
| 6 | Vent fort / tempête |
| 7 | Temps éblouissant |
| 8 | Temps couvert |
| 9 | Autre |

#### `col` — Type de collision
| Code | Signification |
|------|---------------|
| 1 | Deux véhicules - frontal |
| 2 | Deux véhicules - par l'arrière |
| 3 | Deux véhicules - par le côté |
| 4 | Trois véhicules et plus - en chaîne |
| 5 | Trois véhicules et plus - collisions multiples |
| 6 | Autre collision |
| 7 | Sans collision |

### A2. Variables de `lieux`

#### `catr` — Catégorie de route
| Code | Signification |
|------|---------------|
| 1 | Autoroute |
| 2 | Route nationale |
| 3 | Route départementale |
| 4 | Voie communale |
| 5 | Hors réseau public |
| 6 | Parc de stationnement ouvert |
| 7 | Routes de métropole urbaine |

#### `circ` — Régime de circulation
| Code | Signification |
|------|---------------|
| 1 | À sens unique |
| 2 | Bidirectionnelle |
| 3 | Chaussées séparées |
| 4 | Voies d'affectation variable |

#### `nbv` — Nombre de voies de circulation (numérique direct)

#### `surf` — État de la chaussée
| Code | Signification |
|------|---------------|
| 1 | Normale |
| 2 | Mouillée |
| 3 | Flaques |
| 4 | Inondée |
| 5 | Enneigée |
| 6 | Boue |
| 7 | Verglacée |
| 8 | Corps gras |
| 9 | Autre |

#### `situ` — Situation de l'accident
| Code | Signification |
|------|---------------|
| 1 | Sur chaussée |
| 2 | Sur bande d'arrêt d'urgence |
| 3 | Sur accotement |
| 4 | Sur trottoir |
| 5 | Sur piste cyclable |
| 6 | Autre |

#### `vma` — Vitesse maximale autorisée (km/h, numérique direct, **apparue en 2023**)

### A3. Variables de `vehicules`

#### `catv` — Catégorie du véhicule (liste **partielle** — "quelques codes fréquents")
| Code | Véhicule |
|------|----------|
| 1 | Bicyclette |
| 2 | Cyclomoteur |
| 3 | Voiturette |
| 7 | Véhicule léger (voiture) |
| 10 | Utilitaire léger |
| 13 | Poids lourd |
| 14 | Autocar |
| 15 | Autobus |
| 30 | Motocyclette |
| 33 | Tracteur routier |
| 34 | Tracteur agricole |

#### `choc` — Point de choc principal
| Code | Signification |
|------|---------------|
| 0 | Aucun |
| 1 | Avant |
| 2 | Avant droit |
| 3 | Avant gauche |
| 4 | Arrière |
| 5 | Arrière droit |
| 6 | Arrière gauche |
| 7 | Côté droit |
| 8 | Côté gauche |
| 9 | Chocs multiples |

#### `manv` — Manœuvre principale (liste **partielle** — "quelques codes fréquents")
| Code | Signification |
|------|---------------|
| 0 | Inconnue |
| 1 | Sans changement de direction |
| 2 | Même sens même file |
| 9 | Tourne à droite |
| 13 | Dépassement |
| 15 | Changement de file |
| 17 | Demi-tour |
| 19 | Stationnement |
| 21 | Évitement |
| 23 | Marche arrière |

### A4. Variables de `usagers`

#### `catu` — Catégorie d'usager
| Code | Signification |
|------|---------------|
| 1 | Conducteur |
| 2 | Passager |
| 3 | Piéton |

#### `grav` — Gravité des blessures (BAAC 2022-2024)
| Code | Signification |
|------|---------------|
| 1 | Indemne |
| 2 | Tué |
| 3 | Blessé hospitalisé |
| 4 | Blessé léger |

#### `sexe`
| Code | Signification |
|------|---------------|
| 1 | Homme |
| 2 | Femme |

#### `trajet` — Motif du déplacement
| Code | Signification |
|------|---------------|
| 1 | Domicile ↔ travail |
| 2 | Domicile ↔ école |
| 3 | Courses |
| 4 | Utilisation professionnelle |
| 5 | Loisirs |
| 9 | Autre |

#### `secu1`, `secu2`, `secu3` — Équipements de sécurité
| Code | Signification |
|------|---------------|
| 0 | Aucun |
| 1 | Ceinture |
| 2 | Casque |
| 3 | Dispositif enfant |
| 8 | Gilet réfléchissant |
| 9 | Autre équipement |

### A5. Variables clés pour la prédiction de `grav` (recommandation du LLM)

`lum`, `atm`, `agg`, `int`, `col`, `catr`, `surf`, `vma`, `catv`, `manv`, `sexe`, `âge` (calculé depuis `an_nais`), `catu`

---

## Zone B — Analyse et idées générées

### B9. 🔴 PROBLÈME — Listes partielles pour `catv` et `manv`

**Identifié le :** 2026-06-25

Le LLM précise explicitement que les listes de `catv` et `manv` ne montrent que "quelques codes fréquents". **Il manque des codes.** Par exemple :
- `catv` : Où sont les trottinettes électriques ? Les EDPM (Engins de Déplacement Personnel Motorisés) ajoutés récemment ?
- `manv` : Les codes 3-8, 10-12, 14, 16, 18, 20, 22, 24+ ne sont pas listés.

**Impact MLOps :** Si le `value_dictionaries.yaml` est incomplet, le Data Contract laissera passer des valeurs inconnues sans alerter. Le pipeline doit gérer les codes non documentés avec un fallback (ex: logger un warning, catégoriser en "Autre").

**Action :** Compléter depuis la documentation officielle ONISR (PDF `description-des-bases-de-donnees-onisr`).

### B10. 🔴 PROBLÈME — Le code `-1` (valeur manquante) est absent du dictionnaire

**Identifié le :** 2026-06-25

Dans notre [data_inventory_archive.md](file:///Users/nolll/.gemini/antigravity/brain/10b271a9-5646-4286-b482-9f27ac791062/data_inventory_archive.md), nous avons identifié que `-1` est utilisé comme valeur manquante dans certaines colonnes et certaines années. **Le dictionnaire de la Partie 3 ne mentionne jamais `-1`.** C'est un trou de documentation dangereux :
- Si `-1` arrive dans `grav`, est-ce un "Indemne - 1" ou un "Non renseigné" ?
- Le pipeline doit traiter `-1` **avant** le décodage, sinon le décodage échouera silencieusement.

**Action :** Dans le `harmonizer.py`, l'étape "Unification des valeurs manquantes" (Étape 4 du [harmonisation_plan.md](file:///Users/nolll/.gemini/antigravity/brain/10b271a9-5646-4286-b482-9f27ac791062/harmonisation_plan.md)) doit s'exécuter **AVANT** l'étape de décodage.

### B11. 🟡 OBSERVATION — `hrmn` (heure) est absent de la feature list recommandée

**Identifié le :** 2026-06-25

Le LLM recommande 13 variables clés pour prédire `grav` (section A5), mais **`hrmn` n'y figure pas**. C'est surprenant car l'heure est généralement un prédicteur fort (accidents de nuit = plus graves, heures de pointe = plus fréquents mais moins mortels).

**Hypothèse :** Le LLM a peut-être exclu `hrmn` à cause de la corruption documentée (2019-2022). Mais c'est une raison de **nettoyer** la variable, pas de l'ignorer.

**Action :** Ajouter `hrmn` (transformé en features cycliques `hour_sin`, `hour_cos`) à la liste des features du modèle, mais uniquement sur les années où la donnée est fiable.

> [!IMPORTANT]
> **[⚠️ ÉVOLUTION de B6]** — L'idée B6 (Partie 2, "le décodage ETL = value_dictionaries.yaml") est maintenant **concrétisée** par la Partie 3 : nous avons le contenu réel du dictionnaire. Mais il est **incomplet** (B9) et ne gère pas les valeurs manquantes (B10).

### B12. 🟡 OBSERVATION — Stabilité temporelle des codes non documentée

**Identifié le :** 2026-06-25

Le dictionnaire ne précise pas **depuis quand** chaque code existe. Par exemple :
- `catr = 7` (Routes de métropole urbaine) — existait-il en 2005 ?
- `catv = 50+` (trottinettes, EDPM) — ajouté quand ?
- `secu` codé différemment avant 2023 (1 colonne vs 3)

Si un code apparaît en 2019 mais pas en 2010, un modèle entraîné sur 2005-2024 verra un déséquilibre artificiel (la catégorie semble rare alors qu'elle n'existait juste pas avant).

**Action :** Ajouter un champ `available_since` dans le `value_dictionaries.yaml` pour chaque code.

---

## Zone C — Statut des idées (Partie 3/20)

| ID | Idée | Statut | Pertinence MLOps |
|----|------|--------|------------------|
| B9 | Listes partielles catv/manv | 🟢 Active | 🔴 Critique — Data Contract incomplet |
| B10 | `-1` absent du dictionnaire | 🟢 Active | 🔴 Critique — Ordre des étapes du pipeline |
| B11 | `hrmn` absent de la feature list | 🟢 Active | 🟡 Feature engineering |
| B12 | Stabilité temporelle des codes | 🟢 Active | 🟡 Gestion du drift historique |

---

# Partie 4/20 — Jointures, Duplication & Agrégation

**Date de réception :** 2026-06-25 10:04

---

## Zone A — Contenu brut archivé

### A1. Relations et clés de jointure

| Table | Clé de jointure |
|-------|----------------|
| `caract` ↔ `lieux` | `Num_Acc` |
| `caract` ↔ `vehicules` | `Num_Acc` |
| `vehicules` ↔ `usagers` | `Num_Acc` + `id_vehicule` |

### A2. Jointures SQL

```sql
-- Jointure complète
SELECT *
FROM caract c
LEFT JOIN lieux l
    ON c.Num_Acc = l.Num_Acc
LEFT JOIN vehicules v
    ON c.Num_Acc = v.Num_Acc
LEFT JOIN usagers u
    ON v.Num_Acc = u.Num_Acc
   AND v.id_vehicule = u.id_vehicule;
```

### A3. Jointures Pandas (étape par étape)

```python
import pandas as pd

caract = pd.read_csv("caract-2024.csv")
lieux = pd.read_csv("lieux-2024.csv")
vehicules = pd.read_csv("vehicules-2024.csv")
usagers = pd.read_csv("usagers-2024.csv")

# Étape 1 : accident + lieu
accident_lieu = caract.merge(lieux, on="Num_Acc", how="left")

# Étape 2 : + véhicules
accident_veh = accident_lieu.merge(vehicules, on="Num_Acc", how="left")

# Étape 3 : + usagers (clé composite !)
df_final = accident_veh.merge(
    usagers,
    on=["Num_Acc", "id_vehicule"],
    how="left"
)
```

### A4. Problème de duplication (confirmé par le LLM)

Exemple avec accident `202400000005` :
- LIEUX : 2 lignes (même commune, 2 voies)
- VÉHICULES : 4 lignes (A01, B01, C01, D01)
- Jointure directe : **2 × 4 = 8 lignes** × nombre d'usagers

> Le nombre de lignes peut exploser.

### A5. Solution : Agrégation avant chargement (FACT_ACCIDENT)

```python
# Nombre de véhicules par accident
fact_veh = (
    vehicules
    .groupby("Num_Acc")
    .size()
    .reset_index(name="nb_vehicules")
)

# Nombre d'usagers
fact_usagers = (
    usagers
    .groupby("Num_Acc")
    .size()
    .reset_index(name="nb_usagers")
)

# Nombre de tués
fact_tues = (
    usagers[usagers["grav"] == 2]
    .groupby("Num_Acc")
    .size()
    .reset_index(name="nb_tues")
)

# Table de faits finale
fact_accident = (
    caract
    .merge(fact_veh, on="Num_Acc", how="left")
    .merge(fact_usagers, on="Num_Acc", how="left")
    .merge(fact_tues, on="Num_Acc", how="left")
)
```

Résultat : **une ligne par accident** avec les principaux indicateurs analytiques.

---

## Zone B — Analyse et idées générées

### B13. 🟢 RÉUTILISABLE — Les requêtes SQL sont le squelette du schéma PostgreSQL

**Identifié le :** 2026-06-25

Les requêtes SQL de la section A2 ne sont pas que pédagogiques — elles sont directement réutilisables pour :
- Créer les vues matérialisées dans PostgreSQL (Phase 3)
- Écrire les migrations de schéma (`CREATE TABLE`, `CREATE VIEW`)
- Tester les jointures dans le DW après chargement des Parquet harmonisés

**À réaliser :** Stocker ces requêtes dans `sql/views/` du projet.

### B14. 🟡 OBSERVATION — LEFT JOIN = Lignes fantômes potentielles

**Identifié le :** 2026-06-25

Toutes les jointures utilisent `LEFT JOIN` / `how="left"`. C'est correct pour ne pas perdre d'accidents, mais cela crée des lignes avec des `NaN` si :
- Un accident n'a aucun véhicule enregistré (possible ? hit-and-run ?)
- Un véhicule n'a aucun usager enregistré

**Impact MLOps :** Le pipeline doit vérifier après jointure que les `NaN` créés par le LEFT JOIN sont attendus (donnée réellement manquante) et non pas le signe d'un problème de clé de jointure (ex : `id_vehicule` qui ne matche pas entre `vehicules` et `usagers`).

**Action :** Ajouter un Data Contract post-jointure : `assert df_final['id_vehicule'].isna().mean() < 0.01`

> [!IMPORTANT]
> **[⚠️ ÉVOLUTION de B1]** — Le LLM **confirme lui-même** le piège de duplication identifié en B1 (Partie 1). Il utilise exactement le même exemple (2 lieux × 4 véhicules = 8 lignes). **B1 est maintenant validée par la source elle-même.** La solution proposée (agrégation en FACT_ACCIDENT) est le code de la section A5.

### B15. 🔴 CRITIQUE — Le code d'agrégation A5 est le squelette du `harmonizer.py`

**Identifié le :** 2026-06-25

The code Pandas de la section A5 n'est pas un simple exemple pédagogique — c'est **le cœur de la logique d'agrégation** du pipeline MLOps. Il doit être :
1. Paramétré (quelles mesures agréger ? configurable dans un YAML)
2. Testé unitairement (`test_fact_accident_no_duplicates()`)
3. Complété avec d'autres agrégations utiles au ML :
   - `nb_blesses_hospitalises` = `usagers[grav == 3].groupby(...)`
   - `gravite_max` = `usagers.groupby("Num_Acc")["grav"].min()` (min car 2=tué est la valeur la plus grave)
   - `nb_pietons` = `usagers[catu == 3].groupby(...)`
   - `age_conducteur_moyen` = calculé depuis `an_nais`

**À réaliser Phase 1 :** Transformer ce snippet en fonction testable dans `src/data/aggregator.py`.

> [!IMPORTANT]
> **[⚠️ ÉVOLUTION de B3]** — L'absence de PK dans LIEUX (B3, Partie 1) est maintenant **illustrée concrètement** par l'exemple de duplication de la Partie 4 : Bédoule apparaît 2× dans LIEUX, ce qui double toutes les lignes lors de la jointure. La stratégie d'agrégation (ou de dédoublonnage) de LIEUX est désormais une **priorité** avant toute jointure.

---

## Zone C — Statut des idées (Partie 4/20)

| ID | Idée | Statut | Pertinence MLOps |
|----|------|--------|------------------|
| B13 | SQL réutilisable pour PostgreSQL | 🟢 Active | 🟡 Phase 3 — `sql/views/` |
| B14 | LEFT JOIN = NaN fantômes | 🟢 Active | 🟡 Data Contract post-jointure |
| B15 | Code agrégation = squelette harmonizer | 🟢 Active | 🔴 Phase 1 — `src/data/aggregator.py` |

---

# Partie 5/20 — Pourquoi les jointures & Schéma enrichi

**Date de réception :** 2026-06-25 10:06

---

## Zone A — Contenu brut archivé

### A1. Ce que chaque fichier apporte individuellement

| Fichier | Variables clés | Question isolée |
|---------|---------------|----------------|
| `caract` | date, heure, météo, luminosité, collision, lat/long | Quand et où ? |
| `lieux` | type de route, nb voies, vma, état chaussée | Sur quelle route ? |
| `vehicules` | catégorie, manœuvre, choc | Quel véhicule faisait quoi ? |
| `usagers` | sexe, âge, gravité, place | Qui et comment blessé ? |

### A2. Analyses croisées rendues possibles par les jointures

| Question métier | Tables requises | Variables croisées |
|----------------|----------------|--------------------|
| Accidents graves + pluie ? | `usagers` + `caract` | `grav` × `atm` |
| Routes 90 km/h + dangerosité ? | `lieux` + `usagers` | `vma` × `grav` |
| Motos + blessures graves ? | `vehicules` + `usagers` | `catv` × `grav` |
| Carte des accidents mortels ? | `caract` + `usagers` | `lat/long` × `grav` |

### A3. Schéma en étoile enrichi (5 dimensions)

```
              Dim_Date
                  |
Dim_Lieu --- Fait_Accident --- Dim_Vehicule
                  |
             Dim_Usager
                  |
             Dim_Meteo
```

> [!NOTE]
> **Évolution par rapport aux Parties 1-2 :** `Dim_Meteo` est désormais une **dimension séparée** (et non plus un attribut de `Fait_Accident` ou de `Dim_Lieu`).

### A4. Exemple de requête BI cible

> *Nombre d'accidents mortels, par département et par météo, sur les 3 dernières années*

Implique les dimensions `Dim_Date`, `Dim_Lieu`, `Dim_Meteo` et la mesure `nb_tues` dans `Fait_Accident`.

---

## Zone B — Analyse et idées générées

### B16. 🟡 OBSERVATION — `Dim_Meteo` séparée = Feature Group distinct en MLOps

**Identifié le :** 2026-06-25

Le schéma en étoile sépare désormais la météo en une dimension propre. En MLOps, cela correspond à un **feature group** distinct dans le feature store :
- `feature_group_meteo` : `atm`, `lum` (et potentiellement des features dérivées : `is_night`, `is_rain`, `is_fog`)
- Avantage : si on ajoute une source externe de météo (ex: API Météo-France pour le use case 5 — même s'il est rejeté pour l'instant), on enrichit ce feature group sans toucher aux autres.

**À réaliser :** Organiser les features en groupes logiques dans le pipeline, pas en une seule table plate monolithique.

### B17. 🟢 CONFIRMATION — Les analyses croisées valident les use cases

**Identifié le :** 2026-06-25

Les 4 analyses croisées de la section A2 correspondent directement à nos use cases métier :

| Analyse croisée (Partie 5) | Use case métier (Partie 1 de la discussion principale) |
|---------------------------|-------------------------------------------------------|
| Accidents graves + pluie | Use case 1 (Aide aux urgences) — mais attention au biais chronologique |
| Routes 90 km/h + danger | Use case 4 (Aide infrastructure) |
| Motos + blessures graves | Use case 2 (Scoring zones) + Use case 1 |
| Carte accidents mortels | Use case 2 (Scoring zones à risque) |

Cela confirme que le modèle relationnel BAAC et le schéma DW sont **alignés avec les objectifs ML du projet**.

---

## Zone C — Statut des idées (Partie 5/20)

| ID | Idée | Statut | Pertinence MLOps |
|----|------|--------|------------------|
| B16 | Dim_Météo = feature group séparé | 🟢 Active | 🟡 Architecture feature store |
| B17 | Analyses croisées = validation use cases | 🟢 Active | 🟢 Alignement DW/ML confirmé |

---

# Partie 6/20 — Conception avancée DW (Niveau Entreprise)

**Date de réception :** 2026-06-25 10:20

---

## Zone A — Contenu brut archivé

### A1. Objectif et Grain Fondamental

> "1 ligne = 1 usager impliqué dans un accident. C’est le choix le plus puissant pour l’analyse (car la gravité est au niveau usager)."

### A2. Table de faits cible : `FACT_ACCIDENT_USAGER`

**Clés étrangères :** `date_key`, `accident_key`, `lieu_key`, `vehicule_key`, `usager_key`
**Mesures / Dimensions dégénérées :** `nb_accident = 1`, `gravite`, `age`, `sexe`, `catu`, `catv`, `atm`, `lum`, `int`, `col`, `vma`, `agg`, `vitesse_route`, `nb_vehicules_accident`, `nb_usagers_accident`.

### A3. Dimensions et enrichissements métier (Feature Engineering)

| Dimension | Colonnes ajoutées / transformées |
|-----------|----------------------------------|
| **DIM_DATE** | `periode_jour` (matin/aprem/nuit), `weekend` (0/1) |
| **DIM_LIEU** | `zone_danger` (urbain dense, route rapide, zone rurale) |
| **DIM_VEHICULE** | `is_motorise` (0/1), `is_deux_roues`, `is_lourd` |
| **DIM_USAGER** | `tranche_age`, `age_bucket` (0-17, 18-24, 25-44, 45-64, 65+) |
| **DIM_CONDITIONS** | `lum` → jour/nuit, `atm` → normal/pluie/neige/brouillard |
| **DIM_ACCIDENT** | `type_accident` (mortel/corporel), `densite_accident` (urbain/rural) |

### A4. Optimisations Pro (Niveau entreprise)

1. **Slowly Changing Dimension (SCD2)** pour garder l'historique sur les usagers et véhicules.
2. **Indexation** sur `num_acc`, `departement`, `gravite`.
3. **Partitionnement** de `FACT_ACCIDENT_USAGER` par année et département.
4. **Dimensions avancées** : `DIM_RISQUE` (score calculé ML).

---

## Zone B — Analyse et idées générées

### B18. 🔴 CONTRADICTION LLM — Grain `FACT_ACCIDENT` vs `FACT_ACCIDENT_USAGER`

**Identifié le :** 2026-06-25

Dans la Partie 4, le LLM recommandait explicitement de créer `FACT_ACCIDENT` avec le grain "1 ligne = 1 accident" pour éviter les doublons.
Dans la Partie 6, le LLM change d'avis : "Grain fondamental : 1 ligne = 1 usager impliqué dans un accident" et crée `FACT_ACCIDENT_USAGER`.

**Impact MLOps :** En fait, le grain "Usager" est **exactement** ce dont on a besoin pour la Feature Matrix du Machine Learning ! Le LLM a "accidentellement" conçu notre Feature Matrix en pensant faire un Data Warehouse de niveau entreprise.

**Action :** Conserver la recommandation de la Partie 6. Notre pipeline construira une large table aplatie au grain "Usager". La table `FACT_ACCIDENT` (grain accident, Partie 4) restera un simple sous-produit agrégé pour les dashboards macroscopiques.

### B19. 🟢 FEATURE ENGINEERING — Excellente liste de transformations

**Identifié le :** 2026-06-25

Le LLM liste des transformations très pertinentes pour le ML :
- Binarisation : `is_motorise`, `weekend`, `is_deux_roues`
- Discrétisation : `age_bucket`, `periode_jour`
- Regroupement : `zone_danger`

**Action :** Intégrer exactement ces transformations dans le `src/features/build_features.py` de notre pipeline MLOps Phase 1.

### B20. 🔵 BI-ONLY / HORS SCOPE — SCD2 et SCD sur usagers/véhicules

**Identifié le :** 2026-06-25

Le LLM recommande du SCD2 (Slowly Changing Dimensions) pour garder l'historique des usagers et des véhicules.
**Problème métier :** Dans la base BAAC, un usager ou un véhicule n'est documenté qu'au moment précis de l'accident. Il n'y a pas d'historique de l'usager avant/après l'accident dans ce jeu de données (les données sont anonymisées, pas de PK globale de la personne). Le SCD2 n'a aucun sens ici.

**Action :** Rejeter l'implémentation du SCD2 (recommandation non suivie, ajoutée au backlog). Par contre, conserver le partitionnement (par année) qui est une excellente pratique MLOps.

---

## Zone C — Statut des idées (Partie 6/20)

| ID | Idée | Statut | Pertinence MLOps |
|----|------|--------|------------------|
| B18 | Contradiction LLM sur le grain FACT | 🟢 Active | 🔴 Le grain "Usager" (Partie 6) valide notre vision Feature Matrix |
| B19 | Feature engineering explicite | 🟢 Active | 🔴 Feature engineering (Phase 1) |
| B20 | SCD2 sur Usagers/Véhicules | ❌ Rejetée | 🔵 BI-only / Incompatible avec les données BAAC |

---

# Partie 8/20 — Conception Data Warehouse (PostgreSQL)

**Date de réception :** 2026-06-25 11:05

---

## Zone A — Contenu brut archivé

### A1. Nouveau schéma en étoile proposé
Le LLM propose un Star Schema centré sur `FACT_ACCIDENT` (1 ligne = 1 accident).
Il éclate la table `caractéristiques` en de multiples micro-dimensions :
- `DIM_WEATHER` (`atm`)
- `DIM_LUMINOSITY` (`lum`)
- `DIM_INTERSECTION` (`int`)
- `DIM_COLLISION` (`col`)

### A2. Script SQL PostgreSQL
Le LLM fournit un script DDL complet (`CREATE TABLE`) pour initialiser le Data Warehouse.
- Dimensions avec `SERIAL PRIMARY KEY`.
- Fait avec `accident_id BIGINT PRIMARY KEY` et des `REFERENCES` (Foreign Keys).
- Les Usagers et Véhicules sont traités comme des dimensions "satellites" non reliées directement au grain central du fait.

---

## Zone B — Analyse et idées générées

### B23. 🔴 CONTRADICTION LLM — Retour au grain `FACT_ACCIDENT`

**Identifié le :** 2026-06-25

Le LLM oscille ! Dans la Partie 6, il nous avait (à juste titre pour le ML) recommandé la table `FACT_ACCIDENT_USAGER`. Ici dans la Partie 8, il re-propose `FACT_ACCIDENT` (grain accident), et avoue ne pas savoir quoi faire des Usagers et Véhicules ("véhicule et usager sont des satellites / factless facts secondaires").

**Impact MLOps :** C'est typique d'une approche purement BI/Reporting. Si la table de faits ne contient pas l'usager, on ne peut pas entraîner de modèle prédictif sur la gravité (qui dépend de l'usager, pas de l'accident !).

**Action :** Nous rejetons fermement ce modèle pour le ML. Nous conservons notre architecture basée sur `FACT_ACCIDENT_USAGER` (Partie 6) alimentée par Feast. Cependant, le script DDL PostgreSQL est utile comme base pour la Phase 3.

### B24. 🔵 SUR-NORMALISATION — Éclatement des conditions

**Identifié le :** 2026-06-25

Le LLM a créé 4 tables de dimensions séparées pour la météo, la lumière, l'intersection et la collision.
**Action :** C'est une approche "Snowflake" inutilement complexe. Dans un Feature Store ou une base analytique moderne, ces colonnes (`lum`, `atm`, `col`, `int`) tiendront très bien dans une dimension consolidée `DIM_CONDITIONS` (ou `DIM_CONTEXTE`), voire directement dans la table de faits dégénérée, pour éviter des JOIN coûteux. Recommandation rejetée.

---

## Zone C — Statut des idées (Partie 8/20)

| ID | Idée | Statut | Pertinence MLOps |
|----|------|--------|------------------|
| B23 | Retour au grain FACT_ACCIDENT | ❌ Rejetée | 🔴 Incompatible avec notre cible MLOps (qui nécessite l'usager) |
| B24 | Micro-dimensions séparées (lum, atm, col) | ❌ Rejetée | 🟡 Sur-ingénierie BI inutile pour un Feature Store ML |

---

# Partie 9/20 — Script ETL Pandas Monolithique

**Date de réception :** 2026-06-25 11:15

---

## Zone A — Contenu brut archivé

### A1. Script Pandas Monolithique
Le LLM propose un script Python unique qui :
- Charge les CSV (`pd.read_csv`).
- Met les colonnes en minuscules (`str.strip().str.lower()`).
- Parse l'heure (`pd.to_datetime(dim_date["hrmn"], format="%H:%M")`).
- Sépare les DataFrames en dimensions (`dim_location`, `dim_weather`, etc.).
- Construit une table `fact_accident` (au grain accident) avec un calcul de `gravite_max`.
- Pousse directement le tout dans PostgreSQL (`to_sql`).

---

## Zone B — Analyse et idées générées

### B25. 🔴 DANGER — L'amnésie du LLM sur la structure (hrmn)

**Identifié le :** 2026-06-25

Le script fait `pd.to_datetime(..., format="%H:%M")` sur la colonne `hrmn`.
**Le problème :** Dans la Partie 3, ce même LLM nous a prévenus qu'avant 2019, `hrmn` est un entier (`1430`) et après 2019 c'est un string (`14:30`). Ce script Pandas va donc lamentablement crasher (ou générer des valeurs nulles) sur les données pré-2019.
**Impact MLOps :** C'est la preuve absolue qu'il nous faut des **Data Contracts** (Phase 1) pour valider le typage avant toute transformation, plutôt qu'un script Pandas "quick & dirty".

### B26. 🟢 CODE UTILE — Nettoyage standardisé des colonnes

**Identifié le :** 2026-06-25

L'idée de forcer `df.columns.str.strip().str.lower()` dès le chargement est une excellente pratique de Data Engineering pour éviter les bugs liés aux espaces cachés dans les noms de colonnes des CSV open data.
**Action :** Ajouté au `harmonisation_plan.md`.

### B27. 🔵 ARCHITECTURE — Monolithe vs Découplage MLOps

**Identifié le :** 2026-06-25

Le script mélange dans le même fichier : l'extraction brute, l'harmonisation, la modélisation BI en étoile, et le chargement BDD.
**Action (Réponse à l'utilisateur) :** Ce script chevauche maladroitement l'harmonisation et le warehouse. En MLOps industriel, on découple rigoureusement : l'harmonisation produit des Parquet propres (Phase 1). Le Feature Store ou le Warehouse consomment ces Parquet a posteriori.

---

## Zone C — Statut des idées (Partie 9/20)

| ID | Idée | Statut | Pertinence MLOps |
|----|------|--------|------------------|
| B25 | Crash silencieux sur hrmn (Amnésie LLM) | 🟢 Active | 🔴 Justifie l'usage obligatoire des Data Contracts |
| B26 | df.columns.str.strip().str.lower() | 🟢 Active | 🔵 Data Engineering (Phase 1) |
| B27 | Script monolithique "fourre-tout" | ❌ Rejetée | 🔴 Anti-pattern MLOps (couplage fort) |

---

# Partie 10/20 — Architecture ETL Incrémental (Airflow)

**Date de réception :** 2026-06-25 11:24

---

## Zone A — Contenu brut archivé

### A1. Pipeline Airflow et CDC
Le LLM propose de passer à une "version industrie" de l'ETL en mettant en place :
- **Airflow** pour orchestrer les tâches (`PythonOperator`).
- Un principe d'**ETL Incrémental** (ne charger que les nouvelles lignes) basé sur un `watermark` stocké en base de données (`last_num_acc`).
- Un DAG quotidien (`@daily`).
- Des recommandations "Expert" (dbt, Delta Lake, Kafka).

---

## Zone B — Analyse et idées générées

### B28. 🔵 ARCHITECTURE — L'ETL Incrémental Quotidien (YAGNI)

**Identifié le :** 2026-06-25

Mettre en place un DAG Airflow quotidien avec un système de watermark complexe est un excellent pattern d'ingénierie pour des bases de données de production vivantes (e.g., e-commerce).
**Le problème :** Notre jeu de données (BAAC) est publié par le gouvernement en **open data une seule fois par an**. Un pipeline incrémental quotidien est donc l'exemple parfait du "YAGNI" (You Aren't Gonna Need It). Un traitement Batch annuel complet est non seulement suffisant, mais beaucoup plus robuste et simple à maintenir pour nous.
**Action :** Idée formellement rejetée pour le moment.

### B29. 🟢 ARCHITECTURE — La couche de transformation (dbt)

**Identifié le :** 2026-06-25

Dans ses "améliorations pro", le LLM mentionne **dbt** (Data Build Tool). C'est une excellente recommandation si on décide d'aller jusqu'au bout de la Phase 3 (Data Warehouse). Au lieu d'utiliser des scripts Pandas (Partie 9) pour charger Postgres, on peut utiliser dbt pour modéliser le Star Schema.
**Action :** Idée placée dans le Backlog (pour la Phase 3).

---

## Zone C — Statut des idées (Partie 10/20)

| ID | Idée | Statut | Pertinence MLOps |
|----|------|--------|------------------|
| B28 | ETL Incrémental Quotidien (Airflow) | ❌ Rejetée | 🟡 YAGNI — Dataset publié annuellement |
| B29 | Utilisation de dbt pour la modélisation | ⏸️ En attente | 🔵 Data Engineering (Phase 3) |

---

# Partie 11/20 — Data Quality Checks & Great Expectations

**Date de réception :** 2026-06-25 11:28

---

## Zone A — Contenu brut archivé

### A1. Data Quality Checks manuels
Le LLM propose de rajouter une tâche de validation au DAG Airflow en écrivant des fonctions Pandas manuelles (`check_unique`, `check_domains`, `check_geo`) et en journalisant les erreurs dans une table SQL `data_quality_log`.
Il détaille les 5 catégories de tests (Unicité, Intégrité, Null, Domain, Cohérence géographique).

### A2. Découverte de Great Expectations et Data Contracts
Dans la section "Niveau Expert", le LLM cite enfin les "Data Contracts (style Netflix)" et recommande la librairie `great_expectations`.

---

## Zone B — Analyse et idées générées

### B30. 🟡 CODE — Les tests Pandas manuels

**Identifié le :** 2026-06-25

Créer des dizaines de fonctions Python à la main pour vérifier si `atm` est entre 1 et 9 est laborieux, difficile à maintenir, et on réinvente la roue.
**Action :** Idée rejetée. En MLOps moderne, on ne code pas ces tests à la main.

### B31. 🟢 ARCHITECTURE — Validation de notre stratégie : Data Contracts & Great Expectations

**Identifié le :** 2026-06-25

Le LLM valide à 100% l'approche que nous avions anticipée dans notre **Harmonisation Plan (Étape 6)** et dans l'Entrée 1 de notre Journal MLOps. L'utilisation de Data Contracts (via Pandera ou Great Expectations) pour bloquer un pipeline en cas d'anomalie de domaine (ex: `grav = 9`) est la fondation de la qualité de la donnée.
**Action :** Idée déjà implémentée dans notre architecture (Étape 6 du plan d'harmonisation).

---

## Zone C — Statut des idées (Partie 11/20)

| ID | Idée | Statut | Pertinence MLOps |
|----|------|--------|------------------|
| B30 | Tests de data quality codés à la main (Pandas) | ❌ Rejetée | 🟡 Réinvention de la roue (anti-pattern) |
| B31 | Great Expectations / Data Contracts | 🟢 Active | 🔵 Cœur du MLOps (Déjà dans notre Harmonisation Plan) |

---

# Partie 12/20 — Dockerisation Airflow & PostgreSQL

**Date de réception :** 2026-06-25 11:39

---

## Zone A — Contenu brut archivé

### A1. Architecture Docker Compose
Le LLM fournit un fichier `docker-compose.yml` complet qui déploie :
- Un conteneur PostgreSQL 15 (`accidents_dw`).
- Les conteneurs Airflow (Init, Webserver, Scheduler) liés à PostgreSQL.
- Des volumes persistants (`postgres_data`) et des volumes liés (`./dags`, `./data`).

### A2. DAG Airflow Complet
Le LLM propose le script `accidents_dag.py` complet qui reprend :
- L'extraction Pandas.
- Le nettoyage (`df.columns.str.lower()`).
- Le Data Quality manuel (les `if duplicates > 0 raise Exception` de la partie 11).
- Le chargement vers la BDD via Pandas `to_sql`.

---

## Zone B — Analyse et idées générées

### B32. 🟢 ARCHITECTURE — Dockerisation de PostgreSQL

**Identifié le :** 2026-06-25

Le LLM utilise Docker Compose pour instancier la base de données PostgreSQL. C'est une excellente pratique de reproductibilité MLOps. Pas besoin d'installer Postgres en dur sur la machine de l'utilisateur.
**Action :** Idée validée. La Phase 3 (Data Warehouse) s'appuiera sur un `docker-compose.yml` léger pour faire tourner la base PostgreSQL.

### B33. 🔴 ARCHITECTURE — L'entêtement Airflow (YAGNI)

**Identifié le :** 2026-06-25

Le LLM continue de pousser son usine à gaz Airflow. Nous avons déjà rejeté l'orchestration quotidienne complexe (B28) pour des données publiées annuellement.
**Action :** Rejet confirmé.

### B34. 🔴 CODE — Le retour en arrière sur la Data Quality

**Identifié le :** 2026-06-25

Dans la Partie 11, le LLM nous avait recommandé "Great Expectations". Ici, dans le code final du DAG, il revient à des `if df.isnull().sum() > 0 raise Exception` écrits en dur. C'est le fameux anti-pattern impératif.
**Action :** Rejet absolu. Nous utiliserons les Data Contracts déclaratifs (Pandera) comme acté.

---

## Zone C — Statut des idées (Partie 12/20)

| ID | Idée | Statut | Pertinence MLOps |
|----|------|--------|------------------|
| B32 | Docker Compose pour PostgreSQL | 🟢 Active | 🔵 Reproductibilité d'infrastructure (Phase 3) |
| B33 | Airflow Dockerisé | ❌ Rejetée | 🟡 YAGNI (Déjà statué) |
| B34 | Tests DQ manuels dans le DAG | ❌ Rejetée | 🔴 Régression vers l'anti-pattern impératif |

---

# Partie 13/30 — Couche de Transformation dbt (Analytics as Code)

**Date de réception :** 2026-06-25 11:43

---

## Zone A — Contenu brut archivé

### A1. Architecture dbt complète
Le LLM fournit l'arborescence et le code complet pour un projet **dbt** (Data Build Tool) structuré selon l'état de l'art :
- `staging/` : Nettoyage SQL de base (`stg_caract.sql`).
- `intermediate/` : Jointures logiques intermédiaires (`int_accidents.sql`).
- `marts/` : Le schéma en étoile final (`dim_temps.sql`, `fact_accidents.sql`).

### A2. Le retour du grain Usager !
Dans le modèle `fact_accidents.sql`, le LLM stipule explicitement :
`👉 Grain : 1 ligne = 1 usager impliqué dans un accident`
Il effectue un `LEFT JOIN` entre `int_usagers` et `int_accidents` en prenant l'usager comme table de base.

### A3. Data Quality déclarative (dbt tests)
Le LLM propose un fichier `schema.yml` contenant des tests déclaratifs : `not_null`, `accepted_values: [1,2,3,4]` pour la colonne `grav`. Il propose aussi des tests SQL custom (`no_future_dates.sql`).

---

## Zone B — Analyse et idées générées

### B35. 🟢 ARCHITECTURE — L'adoption de dbt pour la Phase 3

**Identifié le :** 2026-06-25

Cette partie 13 est l'implémentation concrète de l'idée B29 (mise en attente). Utiliser **dbt** pour transformer les tables brutes dans PostgreSQL en un vrai schéma en étoile est la norme absolue en *Analytics Engineering*. C'est infiniment supérieur aux scripts de transformation Pandas de la Partie 9.
**Action :** Idée validée. La Phase 3 s'appuiera formellement sur dbt.

### B36. 🟢 CONCEPTION — Le LLM se corrige (Victoire du grain Usager)

**Identifié le :** 2026-06-25

Dans la Partie 8, le LLM s'était égaré en proposant une table de faits centrée sur l'Accident (idée rejetée formellement en B23). Ici, il se corrige de lui-même et revient au grain "Usager", ce qui valide totalement notre choix architectural fait pour le ML.

### B37. 🟢 DATA QUALITY — La validation déclarative dans le DW

**Identifié le :** 2026-06-25

Les `dbt tests` proposés (`accepted_values`) sont l'exact équivalent SQL de nos Data Contracts `Pandera` Python. Pandera protège l'ingestion (Phase 1), `dbt` protègera l'entrepôt de données (Phase 3). C'est la confirmation que l'approche déclarative est la seule viable.
**Action :** Idée validée, intégration conceptuelle dans les documents de génèse.

---

## Zone C — Statut des idées (Partie 13/30)

| ID | Idée | Statut | Pertinence MLOps |
|----|------|--------|------------------|
| B35 | Implémentation de dbt (Staging/Marts) | 🟢 Active | 🔵 Analytics Engineering as Code (Phase 3) |
| B36 | Table de faits au grain Usager | 🟢 Active | 🔵 Alignement parfait ML et BI |
| B37 | Tests déclaratifs dbt (`schema.yml`) | 🟢 Active | 🔵 Data Contracts niveau SQL |

---

# Partie 14/30 — Implémentation Great Expectations

**Date de réception :** 2026-06-25 11:47

---

## Zone A — Contenu brut archivé

### A1. Architecture Great Expectations
Le LLM propose de générer toute la structure lourde de Great Expectations via `great_expectations init`, créant les dossiers `expectations/`, `checkpoints/`, `plugins/`, etc.

### A2. Définition des règles métier
Le LLM fournit d'excellentes règles métier explicites :
- **Géographie :** Latitude `[41, 52]` (France), Longitude `[-5, 10]`.
- **Météo/Lumière :** `atm` `[1-9]`, `lum` `[1-5]`.
- **Usagers :** `grav` `[1-4]`, Année de naissance `[1920-2025]`, `sexe` `[1,2]`.
- **Intégrité :** Les numéros d'accidents des usagers doivent exister dans la table caractéristiques.

### A3. Pipeline de validation
Mise en place d'un `Checkpoint` YAML pour valider les données et générer les "Data Docs" (rapports HTML) et envoyer des alertes Slack.

---

## Zone B — Analyse et idées générées

### B38. 🟢 MÉTIER — Règles de validation BAAC explicites

**Identifié le :** 2026-06-25

Les règles proposées par le LLM (ex: filtrer la latitude entre 41 et 52 pour cibler la France métropolitaine, filtrer l'année de naissance entre 1920 et 2025) sont pertinentes et pragmatiques pour le jeu de données BAAC.
**Action :** Idée validée. Nous coderons très exactement ces règles dans notre schéma Pandera lors de la création du script `harmonizer.py`.

### B39. 🟡 ARCHITECTURE — Le poids de Great Expectations vs Pandera

**Identifié le :** 2026-06-25

Le LLM montre bien la lourdeur de Great Expectations. Pour un simple pipeline ETL en Pandas, GE nécessite la création de dizaines de fichiers YAML, de DataContexts, et de suites JSON.
**Action :** Rejet de l'outil GE pour la Phase 1 au profit de Pandera, mais adoption totale de la philosophie et des règles métier (B38) qu'il a générées.

---

## Zone C — Statut des idées (Partie 14/30)

| ID | Idée | Statut | Pertinence MLOps |
|----|------|--------|------------------|
| B38 | Règles métier BAAC (Lat, Âge, Gravité) | 🟢 Active | 🔵 Serviront de base à notre Data Contract |
| B39 | Implémentation technique Great Expectations | ❌ Rejetée | 🟡 Trop lourd pour la Phase 1 (On garde Pandera) |

---

# Partie 15/30 — Over-engineering : Airflow, Redis & Celery

**Date de réception :** 2026-06-25 11:49

---

## Zone A — Contenu brut archivé

### A1. Stack distribuée Airflow
Le LLM propose un `docker-compose.yml` ultra-lourd incluant :
- `redis:7` comme broker de messages.
- `apache/airflow` en mode `CeleryExecutor` avec des workers scalables (`--scale airflow-worker=4`).
- `flower` pour le monitoring de la file d'attente Redis.

### A2. DAG d'exemple avec Parquet
Le LLM modifie son script ETL pour enfin utiliser `.to_parquet()` comme format intermédiaire au lieu de CSV.

---

## Zone B — Analyse et idées générées

### B40. 🔴 ARCHITECTURE — Le paroxysme de la sur-ingénierie (Over-engineering)

**Identifié le :** 2026-06-25

C'est un cas d'école d'anti-pattern métier. Le LLM propose de déployer une infrastructure distribuée (Redis + Celery + Flower) capable de traiter des milliers de requêtes par seconde... pour traiter 4 fichiers CSV de quelques mégaoctets qui ne sont mis à jour **qu'une seule fois par an**.
**Action :** Rejet absolu. C'est l'illustration parfaite de l'importance du MLOps : savoir aligner la complexité de l'infrastructure sur le besoin métier réel.

### B41. 🟢 ARCHITECTURE — La confirmation du format Parquet

**Identifié le :** 2026-06-25

Au milieu de cette usine à gaz, le LLM remplace enfin les `.to_csv()` intermédiaires par des `.to_parquet()`. Cela valide l'architecture que nous avions définie (Étape 8 du Harmonisation Plan) pour le stockage déconnecté (Feature Store Offline).
**Action :** Idée validée (déjà actée).

---

## Zone C — Statut des idées (Partie 15/30)

| ID | Idée | Statut | Pertinence MLOps |
|----|------|--------|------------------|
| B40 | Architecture Distribuée (Redis/Celery) | ❌ Rejetée | 🔴 Sur-ingénierie totale (Overkill massif) |
| B41 | Utilisation de fichiers Parquet intermédiaires | 🟢 Active | 🔵 Format optimal validé |

---

# Partie 16/30 — Data Observability (Apache Superset)

**Date de réception :** 2026-06-25 11:52

---

## Zone A — Contenu brut archivé

### A1. Déploiement Apache Superset
Le LLM fournit un `docker-compose.yml` complet pour déployer Apache Superset (avec sa propre base PostgreSQL). Superset est configuré pour se connecter au Data Warehouse.

### A2. Dashboards de "Data Observability"
Au lieu de se limiter à des KPIs métiers classiques, le LLM propose d'utiliser l'outil de BI pour créer un "Dashboard Qualité Data" (Data Observability) avec des requêtes SQL vérifiant :
- Le taux de complétude des coordonnées géographiques (KPI 1).
- Les valeurs invalides (KPI 3).
- La complétude de la table des véhicules (KPI 5).

### A3. Recommandations de bonnes pratiques BI
Le LLM insiste sur une règle fondamentale : *toujours utiliser les vues SQL générées par dbt, et limiter les jointures dans Superset (les faire dans dbt).*

---

## Zone B — Analyse et idées générées

### B43. 🟢 ARCHITECTURE — Choix de l'outil BI (Apache Superset)

**Identifié le :** 2026-06-25

Superset est un outil Open Source d'entreprise (incubé chez Airbnb/Apache). C'est un excellent choix pour s'interfacer avec notre Data Warehouse PostgreSQL de la Phase 3. Il est plus puissant que Metabase pour les cas d'usage Big Data / MLOps.
**Action :** Idée validée. Nous l'ajoutons formellement à notre architecture cible comme outil de BI.

### B44. 🟢 MLOPS — La "Data Observability" via la BI

**Identifié le :** 2026-06-25

Le LLM transforme un outil de Business Intelligence (Superset) en outil de **Data Observability**. Utiliser le dashboard pour surveiller la santé des données (% de valeurs nulles, anomalies) est une pratique essentielle en MLOps (Monitoring du Data Drift).
**Action :** Idée validée. Les requêtes SQL de qualité sont précieuses et seront conservées pour la Phase 3.

---

## Zone C — Statut des idées (Partie 16/30)

| ID | Idée | Statut | Pertinence MLOps |
|----|------|--------|------------------|
| B43 | Utilisation d'Apache Superset | 🟢 Active | 🔵 Outil BI de référence (Phase 3) |
| B44 | Dashboards de Data Observability | 🟢 Active | 🔵 Monitoring de la qualité des données |

---

# Partie 17/30 — Le mirage du Lakehouse (Iceberg & Trino)

**Date de réception :** 2026-06-25 12:13

---

## Zone A — Contenu brut archivé

### A1. Stack Lakehouse Moderne
Le LLM propose d'abandonner PostgreSQL pour une architecture "Netflix / Uber style" comprenant :
- **MinIO** : Serveur de stockage objet (clone S3) pour héberger les fichiers.
- **Apache Iceberg** : Format de table ouvert pour gérer les métadonnées (Time Travel, évolution de schéma) au-dessus de fichiers Parquet.
- **Trino** : Moteur de requêtes SQL distribué en mémoire pour lire les tables Iceberg et alimenter Superset.

### A2. Connexions et Ingestion
Le LLM fournit les commandes SQL (Trino) pour créer les tables Iceberg avec le `WITH (format = 'PARQUET')` et le code Python (`pyiceberg`) pour y insérer les données.

---

## Zone B — Analyse et idées générées

### B45. 🔴 ARCHITECTURE — Le mirage du Lakehouse (Over-engineering)

**Identifié le :** 2026-06-25

Le LLM tente de nous vendre une stack conçue pour dissocier le stockage et le calcul sur des Pétaoctets de données (Big Data). Mettre en place MinIO, un Metastore Hive, Iceberg et Trino pour lire 4 fichiers CSV qui pèsent 50 Mo par an est un non-sens architectural absolu.
**Action :** Rejet catégorique. Notre Data Warehouse **PostgreSQL** suffit amplement pour stocker et requêter ces volumes. Un Lakehouse complexifierait inutilement le déploiement et la maintenance.

---

## Zone C — Statut des idées (Partie 17/30)

| ID | Idée | Statut | Pertinence MLOps |
|----|------|--------|------------------|
| B45 | Architecture Lakehouse (Iceberg/Trino) | ❌ Rejetée | 🔴 Hérésie architecturale pour notre volumétrie |

---

# Partie 18/30 — Le Grand Récapitulatif et la Simulation Streaming

**Date de réception :** 2026-06-25 12:21

---

## Zone A — Contenu brut archivé

### A1. Synthèse "Niveaux de maturité"
Le LLM fait un grand récapitulatif de toutes ses propositions précédentes (Airflow, Lakehouse, dbt, Superset, Great Expectations) en les classant par niveaux : "Base", "Intermédiaire" et "Avancé industriel".

### A2. Extensions "Niveau Industriel" (Kafka & ML)
Il propose 3 nouvelles pistes :
1. **Machine Learning Layer** : Prédire la gravité des accidents ou faire du clustering de zones dangereuses.
2. **Geo Analytics Avancé** : Utiliser l'extension spatiale PostGIS.
3. **Streaming (Kafka)** : Ingestion temps réel d'accidents (par "simulation").

---

## Zone B — Analyse et idées générées

### B46. 🔴 ARCHITECTURE — La Simulation de Streaming (Kafka)

**Identifié le :** 2026-06-25

Proposer Apache Kafka (une plateforme distribuée de streaming d'événements à faible latence) pour ingérer un historique d'accidents statique de 2023 en faisant une "simulation temps réel".
**Action :** Rejet absolu. Mettre en place un cluster Kafka Zookeeper/KRaft pour faire semblant de recevoir des données en temps réel est un anti-pattern profond en ingénierie MLOps. C'est l'outil parfait pour un tutoriel, mais désastreux pour un vrai système de production orienté Batch/Annuel.

### B47. 🟢 ARCHITECTURE — L'Extension Spatiale (PostGIS)

**Identifié le :** 2026-06-25

Le LLM mentionne PostGIS. Étant donné que les accidents possèdent des coordonnées GPS (lat/long) fournies par l'ONISR, utiliser PostGIS dans notre Data Warehouse PostgreSQL pour faire des calculs de distance ou des Heatmaps géographiques est une excellente piste.
**Action :** Idée validée pour la Phase 3 (Optionnel, mais pertinent).

### B48. 🟢 MLOPS — La Couche ML (Prédiction de gravité)

**Identifié le :** 2026-06-25

Le LLM confirme l'objectif final du projet : entraîner un modèle pour prédire la gravité d'un accident. C'est exactement l'objectif de notre Phase 2 (Feature Store via Feast) qui alimentera l'entraînement.
**Action :** Idée validée (C'est le cœur de notre projet MLOps).

---

## Zone C — Statut des idées (Partie 18/30)

| ID | Idée | Statut | Pertinence MLOps |
|----|------|--------|------------------|
| B46 | Streaming Kafka simulé | ❌ Rejetée | 🔴 Anti-pattern majeur (Simulation de flux) |
| B47 | Extension spatiale PostGIS | 🟢 Active | 🔵 Pertinent pour la BI géographique |
| B48 | Couche Machine Learning | 🟢 Active | 🔵 Objectif final du MLOps |

---

# Partie 19/30 — La Défense du Cas d'Usage (Label Leakage & Runtime)

**Date de réception :** 2026-06-25 12:23

---

## Zone A — Contenu brut archivé

### A1. Débat sur la Validité du Cas d'Usage
Le LLM répond à une critique d'un collègue qui affirmait que le jeu de données BAAC étant "post-mortem" (rempli après l'accident), il ne peut pas servir à entraîner un système "temps réel" d'aide aux urgences.
Le LLM déconstruit cet argument en séparant la phase de *Training* (où l'on apprend les corrélations historiques) et la phase d'*Inference* (où le système opérationnel reçoit des données partielles à T0, lors de l'appel aux secours).

### A2. Reformulation MLOps "Blindée"
Le LLM propose une définition stricte du cas d'usage : *"Estimer la probabilité de gravité d’un accident à partir des premières caractéristiques observables (contexte routier, environnement, type de collision) afin d’aider les services de secours à prioriser leurs interventions."*

---

## Zone B — Analyse et idées générées

### B49. 🟢 MLOPS — Le Paradoxe Temporel (Training vs Runtime)

**Identifié le :** 2026-06-25

C'est l'un des concepts les plus cruciaux en Machine Learning : s'assurer que les features utilisées pour l'entraînement seront *réellement disponibles au moment de l'inférence (T0)*. C'est ce qu'on appelle la prévention du **Label Leakage** (fuite d'information du futur).
Si le modèle s'entraîne sur le diagnostic médical final, il trichera. Il ne doit utiliser que les métadonnées (Lieu, Météo, Type de route, Heure) qui sont effectivement connues de l'opérateur SAMU lors du premier appel téléphonique.
**Action :** Concept brillant. Nous intégrons cette contrainte de "Disponibilité à T0" dans notre document `ml_dataset_genesis.md` et dans notre Registre d'Anti-Patterns.

---

## Zone C — Statut des idées (Partie 19/30)

| ID | Idée | Statut | Pertinence MLOps |
|----|------|--------|------------------|
| B49 | Séparation temporelle Training/Inference (Disponibilité T0) | 🟢 Active | 🔵 Concept MLOps fondamental (Prévention du Label Leakage) |

---

# Partie 20/30 — L'Illusion de la Validation Industrielle (Hype-Driven Development)

**Date de réception :** 2026-06-25 12:27

---

## Zone A — Contenu brut archivé

### A1. Synthèse globale et Félicitations du LLM
Le LLM conclut sur le statut global du projet. Il affirme que le projet est passé du statut de "simple analyse Data Science" à "Plateforme MLOps Industrielle", et qu'il est désormais inattaquable.

### A2. La justification par la Stack Technique
Pour justifier la solidité du projet, le LLM s'appuie sur la présence des 5 couches qu'il a recommandées :
1. Orchestration avec Airflow + Celery + Redis
2. Quality avec Great Expectations
3. Transformation avec dbt
4. BI avec Superset
5. Architecture moderne avec Lakehouse (Iceberg) et Streaming (Kafka)

---

## Zone B — Analyse et idées générées

### B50. 🔴 MLOPS — La Validation par l'Outil (Hype-Driven Development)

**Identifié le :** 2026-06-25

C'est une situation fascinante. Le LLM nous félicite pour la solidité de notre projet... en se basant *uniquement* sur l'adoption d'outils Big Data ultra-tendances (Kafka, Iceberg, Airflow, Great Expectations). Or, **nous avons précisément rejeté 4 de ces 5 couches** car elles constituaient de la sur-ingénierie massive pour notre cas d'usage annuel de 50 Mo.
**Action :** Rejet absolu de cette philosophie. La solidité industrielle d'un projet ne se mesure pas au nombre d'outils "Hype" empilés, mais à l'adéquation parfaite entre la complexité de l'outil et le besoin métier. C'est l'essence même du "Problem-Driven Development" (vs "Hype-Driven Development"). Cette leçon rejoint notre registre des anti-patterns.

---

## Zone C — Statut des idées (Partie 20/30)

| ID | Idée | Statut | Pertinence MLOps |
|----|------|--------|------------------|
| B50 | Validation industrielle par l'accumulation d'outils Hype | ❌ Rejetée | 🔴 Anti-pattern MLOps ultime (Hype-Driven Development) |

---

# Partie 21/30 — La Fuite en Avant Technologique (L'Hétérogénéité des Données)

**Date de réception :** 2026-06-25 12:34

---

## Zone A — Contenu brut archivé

### A1. L'Inventaire des Anomalies
Le LLM fait un inventaire exhaustif du méga-copier-coller initial et découvre (enfin) ce que nous avions déjà identifié dès la Phase 1 : les données BAAC sont extrêmement hétérogènes d'une année à l'autre.
- Noms de colonnes variables (`Num_Acc` vs `Accident_Id`).
- Formats corrompus (`hrmn` contenant des dates en 2021-2022).
- Différences de schémas selon les époques.

### A2. Le Retour de l'Over-Engineering
Face à cette complexité de la donnée (qui est le lot quotidien de tout Data Engineer), le LLM panique et utilise cet argument pour **réintroduire de force toute la stack Big Data** :
- *"Airflow devient indispensable"*
- *"Lakehouse (Iceberg/Delta) devient justifié"*
- *"Great Expectations devient non négociable"*

---

## Zone B — Analyse et idées générées

### B51. 🔴 MLOPS — La Fuite en Avant (Résoudre la logique métier par l'infrastructure)

**Identifié le :** 2026-06-25

C'est l'évolution directe du Hype-Driven Development. Le LLM découvre un problème purement logique et algorithmique (nettoyer des fichiers CSV dont les colonnes changent de nom, ou corriger des dates mal formatées). Sa réaction n'est pas de dire *"il faut écrire un script Python robuste"*, mais *"il faut déployer une infrastructure Lakehouse avec un orchestrateur distribué"*.
**Action :** Rejet catégorique. L'hétérogénéité de la donnée (Data Wrangling) se résout dans le **code** de l'ETL (notre script `harmonizer.py` avec Pandas/Pandera), absolument pas en complexifiant l'infrastructure sous-jacente. Mettre un fichier CSV corrompu dans un cluster Apache Iceberg ne réparera pas le format de la date. Ce biais majeur intègre immédiatement notre registre des Anti-Patterns.

---

## Zone C — Statut des idées (Partie 21/30)

| ID | Idée | Statut | Pertinence MLOps |
|----|------|--------|------------------|
| B51 | Justifier l'infrastructure lourde par la saleté des données | ❌ Rejetée | 🔴 Anti-pattern massif (Fuite en avant technologique) |

---

# Partie 22/30 — L'Architecture Medallion et les Règles de Nettoyage

**Date de réception :** 2026-06-25 12:38

---

## Zone A — Contenu brut archivé

### A1. Architecture Medallion (Bronze/Silver/Gold)
Le LLM propose une architecture classique en 3 couches (Medallion) :
- **Bronze (RAW)** : Les CSV bruts sans aucune modification.
- **Silver (CONFORMED)** : La couche de normalisation (correction des dates, renommage des identifiants).
- **Gold (CURATED)** : Le schéma en étoile (faits et dimensions) prêt pour la BI et le Feature Store.

### A2. Règles de normalisation spécifiques
Le LLM donne des exemples de transformations critiques :
- Unification de l'identifiant (`Num_Acc` vs `Accident_Id`).
- Détection des heures cassées (Si `hrmn` ressemble à `____-__-__`, c'est invalide).
- Création d'un indicateur de résolution géographique (`geo_level`).

---

## Zone B — Analyse et idées générées

### B52. 🟢 ARCHITECTURE — L'Architecture Medallion (Adaptée en local)

**Identifié le :** 2026-06-25

L'architecture Bronze/Silver/Gold est un standard industriel parfaitement valide. Cependant, conformément à notre rejet de la "Fuite en avant infrastructurelle", nous n'allons pas déployer un cluster Iceberg/Delta Lake pour cela.
**Action :** Nous implémentons cette architecture logique via notre système de fichiers local et PostgreSQL :
- **Bronze** = Dossier `/data/raw/` (CSV originaux)
- **Silver** = Dossier `/data/harmonized/` (Généré par notre script Python `harmonizer.py`)
- **Gold** = Base de données PostgreSQL avec transformations `dbt`.

### B53. 🟢 DATA ENGINEERING — Résolution Géographique (`geo_level`)

**Identifié le :** 2026-06-25

Le LLM suggère de créer une variable `geo_level` (latlong, commune, departement) selon les données disponibles, puisque les GPS manquent dans les vieux fichiers. C'est une excellente idée pour la BI (ne pas afficher de points sur une carte si on n'a que le département).
**Action :** Validée. Ajout de cette règle dans notre document `harmonisation_plan.md`.

---

## Zone C — Statut des idées (Partie 22/30)

| ID | Idée | Statut | Pertinence MLOps |
|----|------|--------|------------------|
| B52 | Architecture Medallion (Bronze/Silver/Gold) | 🟢 Active | 🔵 Concept valide, implémenté sans over-engineering |
| B53 | Indicateur de résolution géographique | 🟢 Active | 🔵 Excellente feature de Data Quality |

---

# 📥 Backlog des recommandations non suivies

*Conformément à ta demande, voici la liste des recommandations proposées par le LLM (ou nous-mêmes) mais volontairement laissées de côté pour l'instant. Elles ne sont pas perdues.*

| ID | Recommandation | Source | Raison de la mise en attente |
|----|----------------|--------|------------------------------|
| **B21** | Création d'un SCD2 pour l'historique des usagers | Partie 6 | Incompatible avec l'anonymisation du BAAC (pas de suivi d'un individu dans le temps). |
| **B22** | Création de scripts SQL complets pour PostgreSQL | Partie 6 | On priorise le pipeline Python (Pandas/Polars) pour générer les Parquet d'entraînement d'abord (Phase 1). Le DW PostgreSQL viendra en Phase 3. |
| **B23** | Utilisation d'Airflow | Partie 2 | Trop complexe pour la Phase 1. On l'implémentera en Phase 3. |
| **B28** | ETL Incrémental Quotidien (Airflow) | Partie 10 | Rejeté par principe YAGNI. Le dataset gouvernemental est publié annuellement. Un batch annuel suffit amplement. |
| **B29** | Utilisation de dbt (Data Build Tool) | Partie 10 | Sortie du backlog et officiellement adoptée (voir B35 / Partie 13). |

---

# Journal d'évolution des idées

*Historique chronologique de toutes les mises à jour, évolutions et obsolescences.*

| Date | Partie | ID Idée | Événement |
|------|--------|---------|-----------|
| 2026-06-25 | 1/20 | B1 | 🆕 Créée — Piège de granularité identifié |
| 2026-06-25 | 1/20 | B2 | 🆕 Créée — Double sortie étoile/plate proposée |
| 2026-06-25 | 1/20 | B3 | 🆕 Créée — Absence de PK dans LIEUX signalée |
| 2026-06-25 | 1/20 | B4 | 🆕 Créée — Table vehicules-immatricules orpheline |
| 2026-06-25 | 2/20 | B1 | ⚠️ Évolution — Grain "Accident" confirmé pour DW, grain "Usager" toujours requis pour ML |
| 2026-06-25 | 2/20 | B2 | ⚠️ Évolution — Renforcée par B8 : Option 3 (DW = sous-produit du pipeline ML) recommandée |
| 2026-06-25 | 2/20 | B5 | 🆕 Créée — Grain FACT_ACCIDENT confirme et précise B1 |
| 2026-06-25 | 2/20 | B6 | 🆕 Créée — Convergence décodage ETL / value_dictionaries.yaml |
| 2026-06-25 | 2/20 | B7 | 🆕 Créée — KPI taux de mortalité trompeur (biais d'exposition) |
| 2026-06-25 | 2/20 | B8 | 🆕 Créée — Tension architecturale DW vs MLOps, Option 3 recommandée |
| 2026-06-25 | 3/20 | B6 | ⚠️ Évolution — Dictionnaire maintenant concret mais incomplet (B9) et sans gestion du -1 (B10) |
| 2026-06-25 | 3/20 | B9 | 🆕 Créée — Listes partielles catv/manv, codes manquants |
| 2026-06-25 | 3/20 | B10 | 🆕 Créée — Code -1 absent du dictionnaire, ordre pipeline impacté |
| 2026-06-25 | 3/20 | B11 | 🆕 Créée — hrmn absent de la feature list recommandée |
| 2026-06-25 | 3/20 | B12 | 🆕 Créée — Stabilité temporelle des codes non documentée |
| 2026-06-25 | 4/20 | B1 | ✅ Confirmée — Le LLM confirme lui-même le piège (2 lieux × 4 véh = 8 lignes) |
| 2026-06-25 | 4/20 | B3 | ⚠️ Évolution — Duplication LIEUX illustrée concrètement (Bédoule 2×) |
| 2026-06-25 | 4/20 | B13 | 🆕 Créée — SQL réutilisable pour PostgreSQL Phase 3 |
| 2026-06-25 | 4/20 | B14 | 🆕 Créée — LEFT JOIN = NaN fantômes potentiels |
| 2026-06-25 | 4/20 | B15 | 🆕 Créée — Code agrégation = squelette du harmonizer/aggregator |
| 2026-06-25 | 5/20 | B16 | 🆕 Créée — Dim_Météo séparée = feature group distinct |
| 2026-06-25 | 5/20 | B17 | 🆕 Créée — Analyses croisées valident les use cases ML |
| 2026-06-25 | 6/20 | B18 | 🆕 Créée — Contradiction LLM, le grain FACT Usager (P6) supplante le grain Accident (P4) |
| 2026-06-25 | 6/20 | B19 | 🆕 Créée — Feature engineering explicite recommandé par le LLM |
| 2026-06-25 | 6/20 | B20 | 🆕 Créée — SCD2 rejeté (incohérent avec l'anonymisation BAAC) |
| 2026-06-25 | 6/20 | B21 | 🆕 Créée — Backlog des recommandations non suivies initialisé |
| 2026-06-25 | 7/20 | B22 | 🆕 Créée — Formalisation du modèle relationnel d'ingestion (Hybride) |
| 2026-06-25 | 8/20 | B23 | 🆕 Créée — Contradiction LLM (retour au grain accident), fermement rejetée pour le ML |
| 2026-06-25 | 8/20 | B24 | 🆕 Créée — Éclatement des dimensions rejeté (sur-normalisation BI) |
| 2026-06-25 | 9/20 | B25 | 🆕 Créée — Crash silencieux sur hrmn (justifie les Data Contracts) |
| 2026-06-25 | 9/20 | B26 | 🆕 Créée — Standardisation des noms de colonnes |
| 2026-06-25 | 9/20 | B27 | 🆕 Créée — Anti-pattern monolithique rejeté |
| 2026-06-25 | 10/20 | B28 | 🆕 Créée — Rejet ETL incrémental quotidien (YAGNI) |
| 2026-06-25 | 10/20 | B29 | 🆕 Créée — Mise en attente de dbt pour la Phase 3 |
| 2026-06-25 | 11/20 | B30 | 🆕 Créée — Rejet des tests data quality manuels Pandas |
| 2026-06-25 | 11/20 | B31 | ✅ Confirmée — Le LLM valide notre anticipation des Data Contracts |
| 2026-06-25 | 12/20 | B32 | 🆕 Créée — Validation de Docker Compose pour Postgres |
| 2026-06-25 | 12/20 | B33 | 🆕 Créée — Rejet de l'usine à gaz Airflow Docker |
| 2026-06-25 | 12/20 | B34 | 🆕 Créée — Rejet des tests manuels réintroduits |
| 2026-06-25 | 13/30 | B35 | 🆕 Créée — Adoption officielle de dbt pour la Phase 3 |
| 2026-06-25 | 13/30 | B36 | ✅ Confirmée — LLM valide notre choix (grain = usager) |
| 2026-06-25 | 13/30 | B37 | ✅ Confirmée — Validation des contrats via dbt tests |
| 2026-06-25 | 14/30 | B38 | 🆕 Créée — Récupération des règles métier BAAC |
| 2026-06-25 | 14/30 | B39 | 🆕 Créée — Rejet technique de GE (au profit de Pandera) |
| 2026-06-25 | 15/30 | B40 | 🆕 Créée — Rejet extrême de la stack Redis/Celery (Over-engineering) |
| 2026-06-25 | 15/30 | B41 | ✅ Confirmée — LLM valide le format Parquet intermédiaire |
| 2026-06-25 | 16/30 | B43 | 🆕 Créée — Validation de Superset pour la BI |
| 2026-06-25 | 16/30 | B44 | 🆕 Créée — Récupération des requêtes de Data Observability |
| 2026-06-25 | 17/30 | B45 | 🆕 Créée — Rejet extrême du Lakehouse (Trino/Iceberg) |
| 2026-06-25 | 18/30 | B46 | 🆕 Créée — Rejet de la simulation de streaming Kafka |
| 2026-06-25 | 18/30 | B47 | 🆕 Créée — Validation de l'idée PostGIS pour le DW |
| 2026-06-25 | 18/30 | B48 | ✅ Confirmée — La couche ML correspond à notre Phase 2 |
| 2026-06-25 | 19/30 | B49 | 🆕 Créée — Concept de Disponibilité à T0 (Label Leakage) |
| 2026-06-25 | 20/30 | B50 | 🆕 Créée — Rejet du Hype-Driven Development (Validation par l'outil) |
| 2026-06-25 | 21/30 | B51 | 🆕 Créée — Rejet de la Fuite en Avant (Infra pour pallier la Data Quality) |
