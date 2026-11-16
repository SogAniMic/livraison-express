# ADR-0000 — Où stocker les artefacts du modèle de Machine Learning

- **Statut** : Accepté
- **Date** : 06/10/2026

## Contexte
L'API doit pouvoir recharger un modèle au démarrage sans réentraîner à chaque redéploiement.
Le modèle fait quelques Mo (pipeline scikit-learn sérialisée avec joblib) ; il est écrit peu
souvent (à chaque réentraînement) et lu très souvent (à chaque démarrage d'instance).

## Options considérées
| Option | Avantages | Inconvénients |
|---|---|---|
| A. Répertoire local (volume Docker) | Aucun service à installer | Pas de versionnage fiable |
| B. Système de fichiers réseau | Partage simple entre machines | Accès concurrents pénibles |
| C. Model Registry (MLflow…) | Versionnage natif, rollback | Service supplémentaire à maintenir |

## Décision
**Option A** : un répertoire local, monté comme volume Docker partagé entre le service
`scheduler` (écriture) et le service `api` (lecture seule).

Le `FileModelRepository` écrit quatre fichiers cohérents : `express_delivery_model.joblib`,
`metrics.json`, `features.json` et `model_card.json`. Chaque écriture passe par un fichier
temporaire suivi d'un renommage atomique : l'API ne lit jamais un modèle à moitié écrit, et
détecte une nouvelle révision pour la recharger sans redémarrer.

Évolution probable vers l'option C dès qu'il faudra comparer plusieurs modèles en production
ou en dépasser un million d'utilisateurs.

## Conséquences
- Chaque modèle est identifié par sa *model card* (`model_version`, `trained_at`, métriques),
  exposée sur `GET /v1/model`.
- Pas de rollback de modèle automatique : on réentraîne ou on restaure le volume.
- Le jour où l'option C est adoptée, cette ADR passe au statut « Superseded by ADR-000X ».
  L'abstraction `ModelRepository` permet ce changement sans toucher au reste du code.
