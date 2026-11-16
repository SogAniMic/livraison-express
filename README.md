# livraison-express

[![CI](https://github.com/SogAniMic/livraison-express/actions/workflows/ci.yml/badge.svg)](https://github.com/SogAniMic/livraison-express/actions/workflows/ci.yml)
[![Release](https://github.com/SogAniMic/livraison-express/actions/workflows/release.yml/badge.svg)](https://github.com/SogAniMic/livraison-express/actions/workflows/release.yml)
![Python](https://img.shields.io/badge/python-3.13-blue)
![Licence](https://img.shields.io/badge/licence-MIT-green)

**Prédire si une commande peut être livrée en express dans la journée.**

Projet fil rouge du module *Industrialisation de l'IA dans le cloud* (YNOV Toulouse — M2 Data & IA) :
transformer un notebook expérimental (`notebooks/project_test_v1_final_final2.ipynb`) en
application de production — code propre, API, tests, Docker, CI/CD, base de données,
réentraînement automatique.

```
ERP ⇄ PostgreSQL ──ETL──▶ MongoDB (analytique) ──▶ scheduler ──train──▶ modèle (.joblib)
                                                                           │
                         clients ──HTTPS──▶ reverse proxy ──▶ API FastAPI ◀┘ (rechargement à chaud)
```

## Sommaire
- [Démarrage rapide](#démarrage-rapide)
- [API](#api)
- [Environnements Docker](#environnements-docker)
- [Architecture](#architecture)
- [CI/CD et GitFlow](#cicd-et-gitflow)
- [Décisions d'architecture](#décisions-darchitecture-adr)
- [Travail réalisé par séance](#travail-réalisé-par-séance)

## Démarrage rapide

Sans base de données (données synthétiques du notebook) :

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt && pip install -e .
cp .env.example .env

python -m livraison_express train                     # entraîne et écrit artifacts/
python -m livraison_express predict --file order.json # prédiction locale
python -m livraison_express serve                     # API sur http://127.0.0.1:8000/docs
pytest                                                # tests
```

Avec MongoDB : `ORDER_REPOSITORY_URL=mongodb://localhost:27017` dans `.env`.

| Commande | Rôle |
|---|---|
| `serve [--host --port]` | démarre l'API |
| `train` | entraîne le modèle sur le repository configuré et écrit les artefacts |
| `predict --file order.json` | prédit une commande sans serveur |
| `scheduler [--once]` | réentraîne dès que suffisamment de nouvelles commandes sont arrivées |

## API

Le contrat est [`docs/api/openapi.yml`](docs/api/openapi.yml) ; la documentation interactive
est servie sur `/docs`.

| Méthode | Endpoint | Rôle | Codes |
|---|---|---|---|
| GET | `/health` | le processus est vivant | 200 |
| GET | `/health/ready` | modèle chargé et base joignable | 200 / 503 |
| POST | `/v1/orders` | enregistrer une commande | 202 / 422 |
| GET | `/v1/orders/{order_id}` | relire une commande | 200 / 404 |
| POST | `/v1/predictions` | prédire l'éligibilité | 200 / 422 / 503 |
| GET | `/v1/model` | model card (version, métriques, limites) | 200 / 503 |

```bash
curl -X POST localhost:8000/v1/predictions -H 'Content-Type: application/json' -d @order.json
# {"order_id":"CMD-…","express_eligible":true,"decision":"oui","probability":0.9377,
#  "model_version":"1.0.0","predicted_at":"…","latency_ms":3.1}
```

Une variable absente, en trop (ex. `express_eligible`) ou hors de son domaine renvoie une
**422** au format `{"error": "validation_error", "message": …, "details": […]}`.

## Environnements Docker

| Fichier | Environnement | Contenu |
|---|---|---|
| `docker-compose.test.yml` | **Test** | API + scheduler + MongoDB + simulateur ERP (PostgreSQL) ; données éphémères |
| `docker-compose.prod.yml` | **Production** | image ghcr.io versionnée, MongoDB authentifié, conteneurs durcis, volumes persistants |
| `erp/docker-compose.erp.yml` | Bases seules | PostgreSQL + MongoDB + simulateur ERP fournis en cours |

```bash
# Test : le simulateur remplit MongoDB, le scheduler entraîne, l'API devient « ready »
docker compose -f docker-compose.test.yml up --build
curl localhost:8000/health/ready

# Production
cp .env.prod.example .env.prod   # renseigner les secrets (fichier ignoré par Git)
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

> **Notes d'environnement**
> - MongoDB 8 refuse de démarrer sur les noyaux Linux 6.19 à 7.0.13
>   ([SERVER-121912](https://jira.mongodb.org/browse/SERVER-121912)) : les fichiers compose
>   utilisent `mongo:7.0` par défaut, surchargeable avec `MONGO_IMAGE=docker.io/library/mongo:8`.
> - Les montages de fichiers portent l'option `:z` pour fonctionner sous SELinux (Fedora,
>   RHEL) ; elle est sans effet ailleurs. Le tout fonctionne avec Docker comme avec Podman.

L'image est construite en **multi-stage** : l'étape `test` exécute ruff et pytest pendant le
build ; l'étape `prod` ne contient que le venv et le code (ni tests, ni `.env`, ni
documentation), tourne avec l'utilisateur non-root `10001` et expose uniquement le port 8000.

## Architecture

```
src/livraison_express/
├── domain/            entités et erreurs métier (aucune dépendance technique)
├── core/
│   ├── learning/      features, pipeline, split, entraînement, prédiction, étiquetage
│   ├── container.py   racine de composition (assemble les services)
│   └── retraining.py  politique et boucle de réentraînement
├── infrastructure/
│   ├── order_repository.py / model_repository.py   abstractions (contrats)
│   ├── factory.py                                  choix des implémentations
│   └── implementation/
│       ├── dev/       mémoire, générateur synthétique, fichiers joblib
│       └── mongo/     MongoOrderRepository + ErpOrderMapper
├── api/               FastAPI + schémas du contrat OpenAPI
├── config.py          configuration par variables d'environnement (12-factor)
└── cli.py             serve / train / predict / scheduler
```

Détails : [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## CI/CD et GitFlow

- **Branches** : `main` (versions livrées), `develop`, `feature/*`, `release/*`, `hotfix/*`
  — voir [CONTRIBUTING.md](CONTRIBUTING.md).
- **CI** (`.github/workflows/ci.yml`) à chaque push et PR : `ruff`, `pytest` (avec un
  service MongoDB pour les tests d'intégration), build des étapes `test` et `prod`, smoke test.
- **CD** (`.github/workflows/release.yml`) : un tag `vX.Y.Z` construit et publie
  `ghcr.io/<owner>/livraison-express:X.Y.Z` (+ `X.Y`, `latest`) ; un push sur `develop`
  publie le tag `develop`.
- **Versions** : Semantic Versioning, journal [CHANGELOG.md](CHANGELOG.md) (Keep a Changelog).

Publier une version :

```bash
git switch develop && git switch -c release/1.1.0
# mise à jour de CHANGELOG.md et de __version__, puis :
git switch main && git merge --no-ff release/1.1.0 && git tag -a v1.1.0 -m "v1.1.0"
git switch develop && git merge --no-ff release/1.1.0
git push origin main develop --tags
```

## Décisions d'architecture (ADR)

| ADR | Décision |
|---|---|
| [0000](docs/adr/0000-stockage-artefacts-modele.md) | Artefacts du modèle dans un répertoire local (volume), écriture atomique |
| [0001](docs/adr/0001-plateforme-de-deploiement.md) | Déploiement dans le cloud, région UE |
| [0002](docs/adr/0002-services-cloud.md) | VM + Docker Compose, registre ghcr.io, reverse proxy TLS |
| [0003](docs/adr/0003-strategie-de-deploiement.md) | Blue/Green + rollback, hotfix, shadow pour les modèles |
| [0004](docs/adr/0004-securite-entrees-sorties-et-donnees.md) | Pare-feu, gateway (clé d'API, rate limiting), moindre privilège, conteneurs durcis |
| [0005](docs/adr/0005-source-de-donnees-mongodb.md) | MongoDB (base analytique) plutôt que PostgreSQL (production) |
| [0006](docs/adr/0006-contrat-de-donnees-et-etiquetage.md) | Validation/traduction des données ERP et étiquetage provisoire |
| [0007](docs/adr/0007-orchestration-reentrainement.md) | Réentraînement par un service scheduler (Airflow plus tard) |
| [0008](docs/adr/0008-gitflow-semver-ci-cd.md) | GitFlow, SemVer, GitHub Actions + ghcr.io |

## Travail réalisé par séance

| Séance | Consigne | Réalisation |
|---|---|---|
| 1 — 06/10 | Transformer le notebook en application (Clean Code, SOLID) | `src/livraison_express/`, CLI, API conforme à l'OpenAPI, tests ; métriques identiques au notebook (accuracy 0,768, ROC AUC 0,849) |
| 2 — 09/10 | Finir l'application, ADR plateforme / cloud / stratégie / sécurité | ADR-0001 à 0004 |
| 3 — 26/10 | GitHub + GitFlow, README / CONTRIBUTING / LICENSE / SECURITY / CODE_OF_CONDUCT, Dockerfile, docker-compose, image optimisée et sécurisée, GitHub Actions (tests + image à la release) | fichiers à la racine, `Dockerfile` multi-stage rootless, `.github/workflows/`, ADR-0008 |
| 4 — 29/10 | ADR PostgreSQL vs MongoDB, implémentation d'`OrderRepository`, intégration via l'image Docker fournie, tests sur les nouvelles données, compose Test et Prod, orchestrateur de réentraînement | ADR-0005 à 0007, `infrastructure/implementation/mongo/`, `erp/`, `docker-compose.test.yml`, `docker-compose.prod.yml`, `scheduler` |

## Licence
[MIT](LICENSE)
