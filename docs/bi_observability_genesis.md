# Génèse de la Data Observability : Le choix d'Apache Superset

> [!NOTE]
> **Rôles de ce document "Génèse" :**
> 1. **Boussole architecturale :** Fixer la philosophie de notre monitoring de données (Data Observability vs BI classique).
> 2. **Support de défense :** Justifier le choix technique d'Apache Superset face à ses alternatives (Metabase, Grafana).
>
> *Sujet de ce document :* Le choix de l'outil de restitution finale pour la Phase 3 (Data Warehouse).

## 1. La Philosophie : De la BI à la Data Observability

En Business Intelligence (BI) classique, l'objectif d'un dashboard est purement métier : afficher le nombre d'accidents par département, l'évolution de la mortalité, etc.

En ingénierie **MLOps**, l'objectif premier d'un dashboard est la **Data Observability** (l'observabilité des données). Avant même de fournir des métriques métier, le dashboard doit répondre à des questions critiques pour l'ingénieur :
- Les données géographiques reçues cette année sont-elles complètes ?
- Y a-t-il une anomalie dans le typage des colonnes (Data Drift) ?
- Les jointures du Data Warehouse génèrent-elles des orphelins ?

## 2. Le Choix Technologique : Apache Superset

Pour répondre à ce besoin, nous devons nous brancher sur notre Data Warehouse (PostgreSQL / dbt) et écrire des requêtes SQL complexes de diagnostic.

### Analyse des alternatives

| Outil | Cas d'usage idéal | Pourquoi nous le rejetons ici |
|-------|-------------------|--------------------------------|
| **Grafana** | Monitoring IT (CPU, RAM, Serveurs), Séries temporelles (Prometheus). | Très mauvais pour l'exploration de données tabulaires relationnelles complexes (SQL/Data Warehouse). |
| **Metabase** | BI "Self-service" ultra-simple pour les profils non-techniques. | Moins performant sur les requêtes SQL complexes, l'interface montre ses limites sur des usages "Big Data". |

### Pourquoi Apache Superset ?

**Apache Superset** est l'outil open-source d'entreprise retenu pour notre architecture :
1. **Conçu pour les Data Engineers :** Interface "SQL-First" (SQL Lab) surpuissante, idéale pour écrire des requêtes d'observabilité.
2. **Écosystème MLOps :** S'intègre nativement avec les Data Warehouses modernes et se connecte parfaitement à notre pipeline dbt.
3. **Visualisations riches :** Capacités de visualisation avancées (ex: Heatmaps géographiques pour les coordonnées lat/long des accidents) sans la lourdeur d'outils propriétaires.

## 3. Intégration dans l'Architecture (Phase 3)

Le dashboard Apache Superset vient coiffer l'ensemble de notre architecture MLOps en bout de chaîne :

```text
[ Fichiers CSV BAAC Bruts ]
           ↓
[ Harmonizer Python (Pandera Data Contract) ]
           ↓
[ Base PostgreSQL ]
           ↓
[ Transformations SQL (dbt) ]
           ↓
    📊 APACHE SUPERSET 📊  <-- (Monitoring du Data Drift & MLOps)
```

En actant l'utilisation d'Apache Superset, nous garantissons que tout problème silencieux survenant dans les futures publications du jeu de données BAAC sera immédiatement visible par l'ingénieur MLOps.

---

## 4. Dashboards à Prévoir (Backlog de Monitoring)

Suite à l'analyse des 6 use cases et la création des 3 familles de modèles, les dashboards Superset suivants sont planifiés :

### 4.1 Dashboard Data Quality (Data Observability Pure)
- Taux de valeurs manquantes par colonne et par année
- Détection de la corruption `hrmn` (format date au lieu d'heure)
- Completude des coordonnées GPS (`lat`/`long`) par département
- Répartition `is_metropole` (vérification que le filtre fonctionne)

### 4.2 Dashboard Feature Drift (Surveillance Modèle Famille A)
- Distribution de `atm` (codes météo) année courante vs baseline
- Distribution de `catr` (type de route) — alerte si nouveau code inconnu
- Distribution géographique (`dep`) — alerte si nouveau département
- Évolution du taux de `grav = grave` dans les données (Concept Drift)

### 4.3 Dashboard Performance Série Temporelle (Modèle Famille B)
- Série temporelle observée vs prédite (nb_accidents par jour/semaine)
- Erreur MAE glissante sur les 30 derniers jours
- Alerte si le MAPE dépasse 20%

### 4.4 Dashboard Disponibilité API Météo (Modèle Famille C)
- Taux de disponibilité de l'API externe (Météo-France)
- Nombre d'alertes déclenchées par département sur les 7 derniers jours
- Comparaison alerte déclenchée vs accident observé (validation rétroactive)

### 4.5 Dashboard Observabilité Système (Latence & Inférence)
*Inspiré de l'architecture OOP Rakuten.*
- **Monitoring intrinsèque de latence :** Séparation du temps de Feature Engineering (`t_feat`) vs Inférence pure (`t_predict`).
- **Taux de Fallback :** Pourcentage des requêtes ayant déclenché le modèle de secours (ex: MLP) au lieu du modèle principal (ex: Stacking) suite à une erreur (ex: Out of Memory, Timeout).
- **Consommation mémoire / CPU** des microservices de prédiction (FastAPI) pour anticiper le scaling.

### 4.6 Dashboard Résilience & Disaster Recovery (Garantie de Reprise)
- **Statut des Backups :** Succès/Échec quotidien du dump `PostgreSQL`, de la copie des artefacts `MLflow` (`mlruns/`) et du stockage `DVC`.
- **Taille des Sauvegardes :** Suivi de la taille en octets des dumps pour détecter les anomalies (ex: sauvegarde vide, chute bruteale ou augmentation suspecte).
- **Âge du Dernier Backup (RPO) :** Indicateur visuel de fraîcheur de la dernière sauvegarde par rapport à l'objectif cible (RPO = 24h).
- **Date du Dernier Test de Restauration :** Alerte visuelle si aucun test de restauration à blanc réussi n'a été exécuté depuis plus de 30 jours.

### 4.7 Dashboard Haute Disponibilité & Performance Active (Résilience Inférence)
- **Monitoring du Load Balancer (LB Skew) :** Distribution de charge en pourcentage (%) entre les instances `FastAPI` de production pour détecter les déséquilibres de routage.
- **Activité des Health Checks :** Taux de flapping des conteneurs, nombre d'instances déclarées défaillantes (unhealthy) et retirées temporairement du pool par le Load Balancer.
- **Indicateurs de Latence Active (P95/P99) :** Suivi en continu de la latence de réponse HTTP de l'API `FastAPI` et alertes de dégradation progressive (latence > 500 ms).
- **Latence et Métriques de Réplication PostgreSQL :** Retard de réplication physique en octets/secondes (`pg_stat_replication`) et statut de synchronisation du serveur secondaire.
- **Routines d'Auto-scaling :** Nombre de conteneurs de serving actifs, alertes d'auto-scaling trop agressif (thrashing) ou trop lent.
- **Activité de Graceful Degradation (Fallbacks Actifs) :** Nombre et ratio de requêtes traitées sous mode dégradé (ex: sans météo car API externe injoignable, fallback cache Feast local).
- **Statut de Matérialisation Feast (Online Store Parity) :** Temps d'exécution du dernier `feast materialize`, taux d'éviction `Redis` pour dimensionnement, fraîcheur des données de serving et détection d'écarts de hash/lignes entre l'Offline Store et l'Online Store.

### 4.8 Dashboard Meta-Monitoring & Business Alignment (Santé du Monitoring & KPIs Métier)
- **Heartbeat & Statut Prometheus/Sentry :** Indicateur visuel d'activité du collecteur de métriques et du serveur d'alerting (détection du monitoring hors-service).
- **Taux de Faux Positifs / Faux Négatifs :** Pourcentage d'alertes résolues sans action (bruit) et volume d'incidents signalés par les utilisateurs avant détection système.
- **Désalignement Métriques Techniques vs Précision Réelle :** Alerte en cas de F1 Score calculé en baisse sur un lot de validation réel alors que les métriques d'infrastructure (CPU, RAM, API HTTP status) sont au vert.
- **Activité des Pipelines & Jobs d'Ingestion :** Temps d'exécution glissant des runs `Prefect` (détection des jobs bloqués ou anormalement longs) et taux de doublons créés lors de relances multiples.
- **KPI d'Usage Métier & Churn Utilisateur :** Suivi du volume hebdomadaire de prédictions demandées (détection d'une chute brutale de trafic indiquant un abandon d'usage) et pertinence finale des décisions prises par les utilisateurs.
- **Détection de Training-Serving Skew & Encodages :** Surveillance de la parité des signatures de features Feast entre l'entraînement et le serving, alertes sur les décalages de preprocessing (`StandardScaler`) et d'encodages catégoriels (`OneHotEncoder`).

### 4.9 Dashboard Observabilité Temporelle & Freshness (Gestion du Temps)
- **Dérive d'Horloge NTP (Clock Offset) :** Différence de temps en millisecondes entre les serveurs et le serveur NTP de référence. Alerte si offset > 100 ms (détection de la dérive).
- **Fraîcheur des Features Feast (Data Freshness) :** Durée écoulée depuis la dernière écriture/matérialisation d'une feature view (obsolescence vs TTL) et comparaison avec les dates d'inférence.
- **Temps de Latence d'Ingestion & Pipelines :** Temps écoulé depuis la dernière mise à jour réussie du dataset source par rapport au schedule `Prefect`.
- **Taux d'Anomalies Temporelles (Futur/Désordre) :** Volume et ratio de lignes de données ingérées ayant des dates futures ou arrivant en dehors des fenêtres d'ordonnancement.
- Statut d'Expiration des Certificats : Nombre de jours restants avant expiration des certificats `SSL`/`TLS` de l'API de serving et des dépendances externes.

### 4.10 Dashboard Qualité des Modèles & Validation (Pipeline ML)
- **Taux de Décalage de Validation Croisée (CV Score Variance) :** Suivi de l'écart-type des métriques (`F1-score`) entre les différents folds de validation croisée. Une variance élevée indique un modèle instable ou un split non représentatif.
- **Erreur de Calibration (Expected Calibration Error - ECE) :** Mesure de la différence entre les probabilités prédites par le modèle et les fréquences réelles observées pour valider la fiabilité de l'indice de confiance.
- **Âge et Fraîcheur du Modèle en Production (Model Age) :** Temps écoulé depuis le dernier réentraînement réussi et promotion du run dans le registre de modèles `MLflow`.
- **Suivi de Non-Régression sur les Slices Critiques :** Comparaison automatique des performances (rappel de la classe "grave") sur les tranches sensibles (nuit, pluie) lors des tests de validation de la `CI/CD`.
- **Taux de Succès des Pipeline Runs :** Suivi du statut d'exécution des étapes de préparation, d'entraînement et d'évaluation, avec alerte immédiate si une étape intermédiaire échoue ou est sautée silencieusement.

### 4.11 Objectifs de Niveau de Service (SLOs) Cibles

Afin d'assurer le suivi de la performance et de la scalabilité opérationnelle, nous établissons les objectifs de niveau de service (`SLO`) suivants pour notre plateforme :

| Indicateur de Service (`SLI`) | Objectif de Performance (`SLO`) | Composant Cible |
| :--- | :--- | :--- |
| Latence moyenne `/predict` | `< 100 ms` | Serving `FastAPI` |
| Latence P95 `/predict` | `< 250 ms` | Serving `FastAPI` |
| Disponibilité globale de l'API | `> 99.9%` | Load Balancer |
| Temps d'ingestion quotidienne BAAC | `< 30 min` | Pipeline `Prefect` / `dbt` |
| Temps de réentraînement du modèle | `< 6 h` | Pipeline `Prefect` d'entraînement |
| Temps de calcul des explications `SHAP` | `< 500 ms` | Modèle d'explicabilité |
| Temps de réponse moyen `PostgreSQL` | `< 50 ms` | Base de données `PostgreSQL` |
| Utilisation `CPU` moyenne | `< 70%` | Infrastructure |
| Utilisation `RAM` maximum | `< 80%` | Infrastructure |
| Occupation de l'espace disque | `< 85%` | Stockage / DB / logs |

### 4.12 Dashboard SRE & Détection d'Anomalies (Prometheus / SRE Engine)
*Surveillance granulaire des composants introduits en Phase 6 et 7.*
- **Monitoring Z-Score :** Suivi en temps réel du Z-Score des features pour détecter les anomalies statistiques et le Data Drift (via `DriftMonitor`). Alerte critique si Z-Score > 3.0.
- **Dégradation Gracieuse (Graceful Degradation) :** État d'activation du `PolicyEngine` et désactivation temporaire de la télémétrie lourde en cas de surcharge (bascule automatique).
- **Télémétrie SRE Haute Fréquence :** Export des métriques Prometheus (`app/api/metrics.py`) : P99 de Latence, saturation CPU/Memory, et requêtes/sec (Throughput).

---

## 5. Architecture d'Observabilité Complète (Couches)

Suite à l'identification de nos angles morts (Entrée 26 du journal), notre architecture d'observabilité se compose désormais de **3 couches complémentaires** :

```text
┌─────────────────────────────────────────────────────────────────────┐
│             ARCHITECTURE D'OBSERVABILITÉ BAAC MLOps                  │
│                                                                       │
│  COUCHE 1 — ERREURS (Actif, Immédiat)                                │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  SENTRY (sentry.io)                                           │  │
│  │  → Capture toute exception non catchée (FastAPI, Batch, Flow) │  │
│  │  → Alerte email/Slack immédiate + StackTrace complète         │  │
│  │  → Monitoring latence P50/P95/P99 par endpoint               │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  COUCHE 2 — FLOWS (Actif, Dashboard)                                 │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  PREFECT (prefect.io)                                         │  │
│  │  → Statut en temps réel de chaque flow (batch_zones, SHAP)   │  │
│  │  → Retries automatiques si la DB est indisponible            │  │
│  │  → Alerte si un flow échoue après 3 retries                 │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  COUCHE 3 — DONNÉES (Passif, Dashboard SQL)                          │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  APACHE SUPERSET (port 8088)                                  │  │
│  │  → Dashboard Data Quality (valeurs manquantes, drift)        │  │
│  │  → Dashboard Feature Drift (atm, catr, dep distributions)   │  │
│  │  → Dashboard Zones à Risque (mart_zones_risque)              │  │
│  │  → Dashboard Latence Inférence (t_feat vs t_predict)        │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  Complémentarité : Sentry = "quelque chose a planté" (alerte)        │
│                   Prefect = "un flow a planté" (orchestration)       │
│                   Superset = "les données ont changé" (tendances)    │
└─────────────────────────────────────────────────────────────────────┘
```

> [!NOTE]
> Ces 3 couches ne se chevauchent pas. Sentry répond à "quoi/où/quand a planté ?", Prefect répond à "est-ce que mes tâches planifiées tournent ?", Superset répond à "est-ce que mes données sont saines ?". Un projet MLOps robuste a besoin des 3.

---

## 6. Manifeste : L'Anatomie Complète de l'Observabilité MLOps

*Cette section sert de boussole théorique globale pour comprendre comment les outils choisis s'inscrivent dans une vision industrielle à 4 piliers.*

L'observabilité n'est pas le "monitoring" (la surveillance).
- Le **monitoring** te dit : *"Le système est cassé."* (Ex: L'API renvoie une erreur 500).
- L'**observabilité** te dit : *"Le système est cassé, **voici pourquoi**, voici ce qui s'est passé juste avant, et voici les systèmes en aval qui vont en souffrir."*

Dans une architecture de niveau industriel, l'observabilité se divise en **4 piliers fondamentaux**. Voici l'anatomie complète de ce qu'ils font, ce qu'ils automatisent, et les angles morts auxquels on ne pense presque jamais.

### PILIER 1 : L'Observabilité Système (Software / IT)
*La plomberie : Est-ce que les tuyaux fuient ?*

- **Les Outils :** Sentry (notre choix), Datadog, Prometheus, Grafana, OpenTelemetry, ELK Stack.
- **Ce qu'ils monitorent :** L'état physique et logiciel des serveurs et microservices. CPU, RAM, Latence réseau (P50, P90, P99), Taux d'erreurs HTTP (4xx, 5xx), utilisation du GPU.
- **Ce qu'ils "checkent" (Valident) :** Les seuils d'alerte (ex: "Le temps de réponse de l'API FastAPI dépasse 500ms pendant plus de 2 minutes").
- **Ce qu'ils automatisent :**
  - La capture complète du contexte lors d'un crash (variables locales, OS, version du code).
  - Le traçage distribué (Distributed Tracing) : affecter un `trace_id` à une requête utilisateur pour voir combien de millisecondes elle a passé dans FastAPI, puis dans BentoML, puis dans PostgreSQL.

**💡 Ce à quoi on ne pense pas (Angles Morts) :**
- **Les fuites de mémoire lentes (Memory Leaks) :** Un modèle ML qui charge de nouveaux tenseurs à chaque requête sans vider la RAM (ex: PyTorch) va crasher au bout de 7 jours. Sans observabilité de la courbe de RAM sur la durée, ce bug est impossible à reproduire en local.
- **Le Rate-Limiting invisible :** L'API externe te bloque après 1000 requêtes. Ton code Python gère l'erreur silencieusement et renvoie des données vides. Tout semble fonctionner, mais le modèle devient aveugle.

### PILIER 2 : L'Observabilité des Données (Data Observability)
*Le carburant : Le pétrole est-il pur ou coupé à l'eau ?*

- **Les Outils :** Monte Carlo, Great Expectations, Soda, Datafold (Théorie d'Entreprise) / **Pandera, dbt tests, Apache Superset** (Notre Réalité).
- **Ce qu'ils monitorent :** La "Data Health". La fraîcheur (Freshness), le volume, le schéma (colonnes ajoutées/supprimées), et la distribution des valeurs.
- **Ce qu'ils "checkent" :** Les Data Contracts. *"La colonne `lat` ne doit contenir que des floats, et le taux de NULL ne doit jamais excéder 5%."*
- **Ce qu'ils automatisent :**
  - Les "Circuit Breakers" : Si les données reçues d'un fournisseur sont corrompues, l'outil coupe automatiquement le pipeline pour empêcher ces données d'empoisonner le Data Warehouse et de fausser le modèle ML.

**💡 Ce à quoi on ne pense pas (Angles Morts) :**
- **Le Data Lineage (Lignée des données) :** Si la colonne `hrmn` (heure) change de format, quels sont les impacts ? Un bon outil te dit : *"Attention, si ça casse, ça va casser la Feature View de Feast, le modèle de Stacking, et le Dashboard Superset n°3"*.
- **Le problème de la "Donnée Silencieusement Fausse" :** Un capteur météo se bloque et renvoie "20°C" pendant tout l'hiver. Le type est bon (Float), il n'y a pas de NULL. Les tests classiques passent. Seule l'observabilité de la **variance** (qui tombe soudainement à zéro) peut détecter cette anomalie.

### PILIER 3 : L'Observabilité des Pipelines (Orchestration)
*L'usine : Les chaînes de montage tournent-elles au bon rythme ?*

- **Les Outils :** Apache Airflow, Dagster, Flyte, **Prefect** (notre choix).
- **Ce qu'ils monitorent :** L'état d'exécution des tâches batch (Ingestion, Nettoyage, Entraînement, Inférence Batch).
- **Ce qu'ils "checkent" :** Les SLAs (Service Level Agreements) temporels et les dépendances (Tâche B ne peut démarrer que si Tâche A réussit).
- **Ce qu'ils automatisent :**
  - Les *Retries* avec *Exponential Backoff* (Réessayer dans 1 min, puis 2, puis 4, puis 8).
  - Les alertes de Timeout : *"Le calcul des valeurs SHAP a pris 4h au lieu de 20 minutes, quelque chose cloche."*

**💡 Ce à quoi on ne pense pas (Angles Morts) :**
- **Les processus Zombies :** Un script cron classique qui plante peut laisser un processus en arrière-plan qui bloque la base de données. Un orchestrateur s'assure de nettoyer la mémoire (teardown).
- **L'Idempotence :** Si un flow Prefect plante à 90% et que tu cliques sur "Restart", va-t-il insérer les données en double dans la base ? L'observabilité du pipeline permet de voir exactement où reprendre sans effets de bord.

### PILIER 4 : L'Observabilité Machine Learning (ML Observability)
*Le Cerveau : Le modèle devient-il sénile ?*

- **Les Outils :** Arize AI, Fiddler, NannyML / **Evidently, MLflow, SHAP** (Notre Réalité).
- **Ce qu'ils monitorent :** Le Data Drift (les données entrantes ont-elles changé ?), le Concept Drift (la relation entre les données et la cible a-t-elle changé ?), le Biais/Équité (Fairness), et l'Explicabilité.
- **Ce qu'ils "checkent" :** Le PSI (Population Stability Index). *"La distribution des routes départementales en 2024 est-elle statistiquement similaire à celle de 2023 ?"*
- **Ce qu'ils automatisent :**
  - Le déclenchement d'un pipeline de réentraînement (`annual_retrain_flow`) si le modèle se dégrade au-delà d'un seuil inacceptable.

**💡 Ce à quoi on ne pense pas (Angles Morts) :**
- **Le cauchemar du "Delayed Ground Truth" (La vérité terrain retardée) :**
  C'est le plus gros défi MLOps. Dans notre projet BAAC, notre API prédit la gravité d'un accident aujourd'hui. Mais on ne saura la **vraie** gravité (le Ground Truth) que l'année prochaine, quand le gouvernement publiera le fichier définitif.
  *Comment monitorer un modèle si on ne peut pas calculer sa précision (Accuracy) en temps réel ?*
  On utilise des **métriques Proxy** : on observe la distribution des prédictions (Prediction Drift). Si le modèle prédisait "Grave" dans 20% des cas l'an dernier, et qu'il prédit soudainement "Grave" dans 60% des cas cette semaine (alors qu'il ne neige pas), on sait que le modèle a vrillé, **avant même d'avoir les vrais labels**.
- **L'Observabilité par "Slice" (Tranche) :** Le modèle peut avoir une précision globale de 90%. Tout a l'air génial. Mais l'observabilité par tranche te montre qu'il a une précision de 98% en plein jour, et de **12% la nuit sous la pluie**. Un monitoring global masque les catastrophes locales.

### L'Évolution dans le Cycle de Vie du Projet (Le Temps)

Les outils d'observabilité n'apparaissent pas au même moment et n'ont pas la même durée de vie :
1. **Avant (La R&D) :** On utilise MLflow (pour comparer les expériences) et ydata-profiling (pour l'EDA). L'observabilité est tournée vers le *passé* (qu'est-ce qui a le mieux marché ?).
2. **Pendant (Le Déploiement) :** On allume Sentry, Prefect et BentoML. L'observabilité est tournée vers le *présent* (mon API est-elle en train de brûler maintenant ?).
3. **Après (La Maturité) :** On se repose sur Evidently et Superset. L'observabilité est tournée vers le *futur* (mon modèle est-il en train de pourrir lentement ? Dois-je le remplacer dans 3 mois ?).

### Le "God Tier" (Ce qui sépare un Senior d'un Architecte)
La finalité ultime de l'observabilité que peu de gens atteignent : **Le FinOps et le ROI**.
L'outil ultime te dit : *"Le modèle V2 est 2% plus précis que le modèle V1, mais il utilise 4 fois plus de CPU via BentoML. Ce gain de 2% nous coûte 4000€ par mois en serveurs AWS. Le ROI est négatif, on rollback (retour arrière) sur la V1."*
C'est là que l'observabilité technique rejoint la stratégie d'entreprise.

---

## 7. La Consommation de l'Observabilité : Push vs Pull

Face à une telle architecture (Sentry, Prefect, Superset, MLflow, Evidently), une angoisse légitime émerge : *« Je ne veux pas avoir 6 onglets ouverts sur mon écran toute la journée pour monitorer mon système »*.

Faut-il tout centraliser dans un outil unique comme Grafana + Prometheus ? C'est ce qu'on appelle en architecture le **"Mythe de la Single Pane of Glass"** (Le mythe du tableau de bord unique).

### Le Piège de la Centralisation Absolue (Grafana)
Grafana est exceptionnel pour afficher des métriques IT (séries temporelles). Mais y forcer tout l'écosystème MLOps est un Anti-Pattern sévère :
- **Pour Sentry :** Grafana peut afficher "12 erreurs", mais pour lire la StackTrace (le code exact qui a planté), il faut l'UI spécialisée de Sentry.
- **Pour Prefect :** Grafana peut dire "Le script a planté", mais pour cliquer sur "Relancer la tâche", il faut l'UI de Prefect.
- **Pour Superset :** Grafana est catastrophique pour explorer des bases de données relationnelles complexes (jointures SQL). Il n'est pas fait pour la BI.
- **Pour MLflow :** Grafana ne sait pas afficher de manière lisible une matrice de confusion ou comparer 50 hyperparamètres d'entraînement.

Vouloir tout centraliser dans Grafana demande des mois de développement pour un résultat final "bricolé" et inférieur aux outils natifs.

### La Vraie Solution : Le paradigme "Push vs Pull"
La vérité de l'observabilité moderne, c'est que **le technicien ne regarde pas ces interfaces au quotidien.** L'angoisse des 6 onglets disparaît si l'on applique la séparation des rôles :

* **Les outils "PUSH" (Ils viennent à toi) :**
  - **Sentry (Erreurs)** et **Prefect (Pipelines)**. Tu n'ouvres **jamais** leur interface le matin. Ils sont configurés pour t'envoyer une alerte Slack ou Email *uniquement* quand quelque chose brûle. Tu ne vas sur leur interface que pour éteindre un incendie.

* **Les outils "ON-DEMAND" (Le Laboratoire) :**
  - **MLflow**, **SHAP** et **ydata-profiling**. Ce sont des outils de laboratoire. Tu ne les ouvres que les jours où tu mets ton casque pour entraîner un nouveau modèle ou faire de la R&D. Ils n'ont rien à faire dans un dashboard de monitoring quotidien.

* **L'outil "PULL" (Le seul que tu regardes vraiment) :**
  - **Apache Superset**. C'est le seul lien permanent. Si tu dois avoir un seul écran allumé au mur (ou un favori dans ton navigateur) pour voir si la base de données va bien, si la qualité (Data Quality) est respectée, et si Evidently n'a pas détecté de *Data Drift*, c'est lui.

**En résumé :**
L'ingénieur MLOps n'a pas 6 tableaux de bord à scruter. Il a **1 canal Slack** (pour les urgences Sentry/Prefect), **1 Superset** (pour la santé métier et données), et une boîte à outils de laboratoire (MLflow/SHAP) qui dort tranquillement jusqu'au jour où il doit écrire du code. C'est l'essence même de l'automatisation pragmatique.

### La Routine Matinale Parfaite

Pour être précis, dans une routine MLOps parfaitement saine, le seul dashboard ouvert proactivement tous les matins est Superset :

1. **Tu arrives le matin :** Tu regardes tes notifications Slack. Si Sentry (erreurs) et Prefect (pipelines) n'ont rien envoyé pendant la nuit, tu sais déjà que le code n'a pas crashé et que les tâches planifiées ont réussi. Tu n'as même pas besoin d'ouvrir leurs interfaces.
2. **Tu ouvres Superset (PULL) :** Avec ton café, tu regardes le tableau de bord métier/données pour t'assurer qu'il n'y a pas de problème métier silencieux (ex: *"tiens, le taux de valeurs manquantes sur la colonne GPS a pris 5% hier, Evidently a remonté un drift mineur"*). C'est de l'analyse proactive.

C'est ça la beauté de l'observabilité bien pensée : les machines te préviennent pour les urgences IT (Push), et toi tu réserves ton temps d'écran pour analyser la valeur métier et la santé des données (Pull).

### Alertes Qualité de Données (Anti-Corruption Silencieuse)
- **NaN Explosion Alert** : Se déclenche si le pourcentage de `NaN` sur une colonne clé augmente de plus de X% par rapport à l'ingestion précédente.
- **Schema Evolution Alert** : Se déclenche si les types de colonnes changent implicitement (`int` -> `float` -> `string`).

### Alertes Sécurité & Accès (Cybersécurité MLOps)
- **API Abuse / Extraction Alert** : Se déclenche si un seul utilisateur/IP appelle l'API de prédiction avec un volume asymétriquement élevé (détection d'extraction de modèle ou DoS).
- **Feature Computation Cost Alert** : Se déclenche si le temps ou le coût de calcul d'une feature explose soudainement (détection d'attaques asymétriques sur le Feature Store).
- **Silent Error Alert (Log Drop)** : Se déclenche si le volume de logs généré chute drastiquement à zéro (détection de coupure d'observabilité par un attaquant).

## Dashboard de Gouvernance MLOps (Data Lineage & Organisation)

Ces alertes et tableaux de bord surveillent l'état de la gouvernance, l'âge des modèles et la vélocité de déploiement, pour empêcher la transformation du système en "boîte noire" legacy.

### 1. Alertes d'Orphanage et Sunsetting
*   **Alerte "Modèle Fantôme"** : Modèle actif sur l'API qui n'a pas reçu de trafic depuis > 30 jours, ou dont le cycle de vie a dépassé 12 mois sans réentraînement.
*   **Alerte de Déviation d'Expérimentation** : Nombre d'expériences (`MLflow Runs`) créées sans `tag` métier ou git commit associé (Mesure l'expérimentation "sauvage" non reproductible).

### 2. Tableaux de Bord de Lineage (Graphe de Dépendances)
*   **Coverage Documentaire & Lineage** : Pourcentage de modèles déployés capables de tracer de manière bidirectionnelle leur origine jusqu'au hash du commit de code, du commit DVC et de la version des features Feast.
*   **Taux de Déploiement CI/CD vs Manuel** : Audit de l'origine des déploiements. Objectif : 100% de déploiements via Service Account (CI/CD), 0% via User Account (manuel).


## Dashboard FinOps MLOps (Économie & Rentabilité)

L'observabilité financière est la condition sine qua non de la survie d'un projet MLOps.

### 1. Alertes d'Hémorragie Cloud
*   **Alerte "Inférence Obèse"** : Le coût de compute (GPU/CPU) par inférence dépasse un seuil de rentabilité fixé avec le métier.
*   **Alerte de Cache Miss Rate** : Taux de recalculs inutiles détectés (requêtes identiques sans cache).

### 2. Tableaux de Bord de Rentabilité
*   **Ratio ROI / Compute** : Suivi du coût opérationnel du pipeline (Prefect + Feast + MLflow) rapporté au nombre de prédictions utiles délivrées.
*   **Volume de Stockage "Froid" vs "Chaud"** : Audit de l'espace disque consommé par le Feature Store et les artefacts MLflow sans politique de rétention claire.


## Dashboard de Qualité Prédictive (Model Decay & Calibration)

Ce tableau de bord est le seul bouclier contre la perte silencieuse de pertinence métier.

### 1. Alertes de Calibration et de Biais
*   **Courbe de Calibration (Brier Score)** : Surveiller que les probabilités prédites (ex: 90% de certitude) reflètent réellement les fréquences empiriques (9 cas sur 10 vrais).
*   **Surveillance des Classes Minoritaires (Slice Monitoring)** : Alertes dédiées aux chutes de Recall sur les segments vitaux (ex: accidents corporels graves) pour éviter le paradoxe du "bon modèle, mauvaise décision".

### 2. Tableaux de Bord de Dérive (Drift)
*   **Target Drift & Concept Drift** : Histogramme comparatif en temps réel de la distribution des prédictions (Mois M vs Mois M-1). Une alerte se déclenche si la moyenne des probabilités d'accident glisse anormalement.
*   **Sensibilité aux Imputations** : Mesure de la proportion de prédictions déclenchées sur des données massivement "fill-forwarded" (valeurs manquantes).


## Dashboard de Confiance & Feedback Utilisateur (Human-in-the-Loop)

Surveiller la relation psychologique entre le modèle et les utilisateurs métiers.

### 1. Alertes d'Amnésie / Biais d'Automatisation
*   **Taux d'Acceptation Aveugle** : Si le taux de validation des recommandations du ML passe subitement de 85% à 99.9%, c'est potentiellement un biais d'autorité (les opérateurs ont arrêté de réfléchir).

### 2. Tableaux de Bord de Rejet (Feedback Loop)
*   **Taux d'Override (Contradiction)** : Pourcentage de fois où l'opérateur humain force une décision contraire à celle du modèle. Un spike indique une perte de confiance massive.
*   **Temps de Résolution par Astreinte** : Mesurer si la "Complexité Cognitive" du système allonge les temps de redémarrage lors d'un incident prod.



### Dashboard 8 : Détection des Black Swans et Cas Extrêmes (Catégorie 23)
**Objectif :** Identifier les scénarios "Hors Distribution" (`OOD`), les défaillances en cascade et les illusions de système fonctionnel.
**Métriques Clés :**
- **Distance de Mahalanobis / Auto-encodeurs :** Score d'anomalie globale sur le vecteur de `features` (détecte les combinaisons explosives ou les valeurs jamais vues).
- **Taux de Cascade (Blast Radius) :** Mesure de la propagation d'une erreur d'un composant (ex: `Feature Store`) aux autres composants (`Serving`, `API`).
- **Indice de Cohérence Multicouche :** Vérification croisée (Cross-Check) entre l'état de l'infrastructure (tout est `UP`), les logs applicatifs et la distribution statistique des prédictions (détecte l'illusion de système fonctionnel).
- **Détection de Thundering Herd :** Monitoring des pics brutaux de `cache miss` suivis d'une saturation de la base de données.
**Bénéfice MLOps :** Évite la paralysie totale du système lors de crises majeures (pandémies, guerres, bugs systémiques) en coupant préventivement les prédictions (Circuit Breaker) si le score `OOD` dépasse un seuil critique.

### 4. Vue "Software Engineering & Reproductibilité" (Gouvernance du Code)
*Dérivée de la Catégorie 4 (Problèmes de Code & Versioning)*
- **Dashboard : Dépendances et Environnements**
  - Distribution des versions de librairies (ex: `scikit-learn` 1.3 vs 1.4) actives en production.
  - Alerte si le hash d'environnement de prod diffère du hash de l'artefact validé en staging.
- **Dashboard : Traçabilité des Inférences**
  - Taux de requêtes sans `trace_id` ou logs d'explications (Visibilité du "Bruit > Signal").
  - Suivi des échecs de pipelines de features (`Feast` désynchronisé) corrélés aux commits applicatifs.

### 5. Vue "Disponibilité & Runtime" (SRE)
*Dérivée de la Catégorie 1 (Crashs Systèmes & Infrastructures)*
- **Dashboard : Santé de l'Infrastructure**
  - Taux global d'erreurs d'API 500 (Crash serveur) et 504 (Timeout).
  - Pression mémoire (RAM) et remplissage disque sur les nœuds critiques (DB, MLflow).
- **Dashboard : Latence et Réseau**
  - Temps de réponse du Feature Store ou des API externes (météo, trafic).
  - Alertes sur l'épuisement de quotas d'API tierces (Erreurs 429).

### Dashboard : Data Silent Corruption (Issu de Cat. 5)
- **Objectif** : Détecter la corruption sémantique des données qui échappe à la supervision technique des orchestrateurs.
- **Panneaux clés** :
  - **Taux de valeurs par défaut/constantes** : Détecte l'anti-pattern de la feature fantôme (ex: remplissage massif par 0 ou NaN).
  - **Analyse de distribution glissante** : Détecte un shift comportemental ou sémantique lent avant qu'il ne détruise la qualité du modèle.
  - **Parité Offline/Online** : Mismatch temporel entre ce qui est stocké dans PostgreSQL et servi dans Redis.
