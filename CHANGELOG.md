# Journal des modifications

Toutes les modifications notables de ce projet sont consignées ici.
Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) ;
versions : [Semantic Versioning](https://semver.org/lang/fr/).

## [Unreleased]

## [1.0.0] - 2026-10-29
Première version livrée : le notebook est transformé en application de production.

### Added
- **Séance 1 (06/10) — du notebook à l'application** : domaine, pipeline scikit-learn,
  entraînement, prédiction, repositories abstraits ; API FastAPI conforme à
  `docs/api/openapi.yml` (`/health`, `/health/ready`, `/v1/orders`, `/v1/predictions`,
  `/v1/model`) avec le format d'erreur `Error` ; CLI `serve`, `train`, `predict` ;
  ADR-0000 (stockage des artefacts).
- **Séance 2 (09/10) — déploiement, release, sécurité** : ADR-0001 à ADR-0004
  (plateforme cloud, services, stratégie Blue/Green, sécurité des entrées/sorties et des
  données).
- **Séance 3 (26/10) — GitHub et Docker** : `Dockerfile` multi-stage (builder / test / prod),
  image non-root sans tests ni secrets avec `HEALTHCHECK` ; GitHub Actions (CI : ruff, pytest,
  build et smoke test ; CD : publication sur ghcr.io à chaque tag `vX.Y.Z` et sur `develop`) ;
  README, CONTRIBUTING, LICENSE (MIT), SECURITY, CODE_OF_CONDUCT, modèles d'issue et de PR,
  Dependabot ; ADR-0008 (GitFlow, SemVer, CI/CD).
- **Séance 4 (29/10) — pipeline de données** : `MongoOrderRepository` sur la base analytique
  (ADR-0005), couche anti-corruption `ErpOrderMapper` et étiquetage provisoire (ADR-0006),
  service `scheduler` de réentraînement et rechargement à chaud du modèle (ADR-0007),
  `docker-compose.test.yml` et `docker-compose.prod.yml`, fichiers manquants du simulateur
  ERP, comptes MongoDB à moindre privilège, tests de contrat et d'intégration MongoDB.

### Changed
- Par rapport à la correction du TP1 : le singleton `Core` est remplacé par une racine de
  composition `Container` construite explicitement (plus d'état global, tests isolés) ;
  imports `src.…` supprimés ; `requirements.txt` réencodé en UTF-8 et limité aux dépendances
  d'exécution (MLflow et `pywin32` retirés de l'image).

[Unreleased]: https://github.com/OWNER/livraison-express/compare/v1.0.0...develop
[1.0.0]: https://github.com/OWNER/livraison-express/releases/tag/v1.0.0
