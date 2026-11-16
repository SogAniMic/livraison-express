# ADR-0007 — Orchestrer le réentraînement du modèle

- **Statut** : Accepté
- **Date** : 29/10/2026

## Contexte
L'ERP alimente MongoDB en continu. Le modèle doit être réentraîné quand suffisamment de
nouvelles données sont disponibles. L'entraînement est un **processus d'exécution**, pas de
construction : il n'a pas sa place dans la CI/CD (qui construit et teste l'application).

## Options considérées
| Option | Avantages | Inconvénients |
|---|---|---|
| A. Pipeline CI/CD planifiée (cron GitHub Actions) | Rien à héberger | Mélange construction et exécution ; les runners n'ont pas accès à la base privée ; artefact à rapatrier |
| B. Apache Airflow | Standard du marché, DAG, reprise sur erreur, interface | Lourd (scheduler, webserver, base de métadonnées) pour **une seule** tâche |
| C. Cron système sur la VM | Très simple | Hors du code, non versionné, non testé |
| D. Service `scheduler` dans l'application (déclenchement sur volume de données) | Versionné, testé, même image que l'API, déclenché par la donnée et non par l'horloge | Fonctions d'un orchestrateur réduites (pas de DAG, pas d'interface) |

## Décision
**Option D** (KISS / YAGNI) : la commande `python -m livraison_express scheduler`, exécutée
par le service `scheduler` des fichiers compose, vérifie toutes les
`RETRAIN_CHECK_INTERVAL_SECONDS` le nombre de commandes disponibles :

- aucun modèle et au moins `MIN_TRAINING_ROWS` commandes → entraînement ;
- au moins `RETRAIN_MIN_NEW_ORDERS` nouvelles commandes depuis le dernier modèle
  (`training_rows` de la model card) → réentraînement ;
- sinon, rien.

Le nouveau modèle est écrit de façon atomique dans le volume partagé ; l'API détecte la
nouvelle révision et la charge sans redémarrage. Un échec (base indisponible, une seule classe)
est journalisé sans arrêter le service ni remplacer le modèle en service.

## Conséquences
- La politique de décision (`core/retraining.py::decide`) est une fonction pure, testée.
- **Évolution vers Airflow** (option B) dès qu'il y aura plusieurs tâches dépendantes
  (ETL, validation des données, entraînement, évaluation, publication) : la commande `train`
  deviendra simplement une tâche du DAG.
- Les seuils sont réglables par environnement (bas en test, plus élevés en production).
