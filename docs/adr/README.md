# Architecture Decision Records (ADR)

Chaque décision d'architecture est enregistrée ici : contexte, options, décision, conséquences.
Une décision n'est jamais effacée : si elle change, l'ADR passe au statut
« Superseded by ADR-XXXX » et une nouvelle ADR est rédigée.

| N° | Décision | Statut | Séance |
|---|---|---|---|
| [0000](0000-stockage-artefacts-modele.md) | Stockage des artefacts du modèle : répertoire local | Accepté | 1 — 06/10/2026 |
| [0001](0001-plateforme-de-deploiement.md) | Plateforme de déploiement : cloud | Accepté | 2 — 09/10/2026 |
| [0002](0002-services-cloud.md) | Services cloud : VM + Docker Compose, registre ghcr.io | Accepté | 2 — 09/10/2026 |
| [0003](0003-strategie-de-deploiement.md) | Stratégie de déploiement : Blue/Green + rollback | Accepté | 2 — 09/10/2026 |
| [0004](0004-securite-entrees-sorties-et-donnees.md) | Sécurisation des entrées/sorties et de l'accès à la donnée | Accepté | 2 — 09/10/2026 |
| [0005](0005-source-de-donnees-mongodb.md) | Source de données : MongoDB (base analytique) plutôt que PostgreSQL | Accepté | 4 — 29/10/2026 |
| [0006](0006-contrat-de-donnees-et-etiquetage.md) | Contrat de données ERP → modèle et étiquetage provisoire | Accepté | 4 — 29/10/2026 |
| [0007](0007-orchestration-reentrainement.md) | Orchestration du réentraînement : service scheduler | Accepté | 4 — 29/10/2026 |
| [0008](0008-gitflow-semver-ci-cd.md) | GitFlow, Semantic Versioning et CI/CD GitHub Actions + ghcr.io | Accepté | 3 — 26/10/2026 |

Modèle à copier : [template.md](template.md).
