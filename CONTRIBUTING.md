# Contribuer à livraison-express

Merci de votre intérêt ! Ce guide explique comment proposer une modification.

## Fonctionnement du projet en bref
- `src/livraison_express/` : application Python (domaine, apprentissage, infrastructure, API, CLI).
- `tests/` : tests unitaires, de contrat, d'API et d'intégration MongoDB.
- `docs/adr/` : décisions d'architecture. **Toute décision structurante passe par une ADR.**
- `docs/api/openapi.yml` : contrat de l'API. **Le contrat fait foi** : le code s'y conforme.

## Signaler un bug ou proposer une évolution
Ouvrez une *issue* avec le modèle correspondant (`.github/ISSUE_TEMPLATE/`) : comment
reproduire, version concernée (`GET /health`), résultat attendu. Une vulnérabilité ne se
signale **jamais** dans une issue publique : voir [SECURITY.md](SECURITY.md).

## Organisation des branches (GitFlow)
| Branche | Rôle | Part de | Fusionne dans |
|---|---|---|---|
| `main` | Versions livrées, taguées `vX.Y.Z` | — | — |
| `develop` | Intégration de la prochaine version | `main` | `release/*` |
| `feature/<sujet>` | Une fonctionnalité | `develop` | `develop` (PR) |
| `release/X.Y.Z` | Stabilisation d'une version | `develop` | `main` + `develop` |
| `hotfix/X.Y.Z` | Correctif urgent en production | `main` | `main` + `develop` |

```bash
git switch develop && git pull
git switch -c feature/ma-fonctionnalite
# ... commits ...
git push -u origin feature/ma-fonctionnalite   # puis Pull Request vers develop
```

## Messages de commit
Format [Conventional Commits](https://www.conventionalcommits.org/fr/) :
`feat: …`, `fix: …`, `docs: …`, `test: …`, `refactor: …`, `ci: …`, `build: …`, `chore: …`.

## Pull Requests
- Une PR = un sujet ; description remplie à partir du modèle.
- CI verte obligatoire (lint + tests + build Docker) et relecture par un développeur senior.
- `CHANGELOG.md` mis à jour dans la section `[Unreleased]`.

## Environnement de développement
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt && pip install -e .
cp .env.example .env
ruff check . && ruff format --check .
pytest                                           # tests unitaires et d'API
MONGO_URI=mongodb://localhost:27017 pytest -m integration   # avec un MongoDB local
```

## Style de code
- Python ≥ 3.12, formatage et lint par `ruff` (configuration dans `pyproject.toml`).
- Principes : SOLID, DRY, KISS, YAGNI. Les dépendances pointent vers les abstractions
  (`OrderRepository`, `ModelRepository`) ; seules `infrastructure/factory.py` et
  `core/container.py` connaissent les classes concrètes.
- Toute nouvelle implémentation d'un repository doit passer les tests de contrat
  (`tests/unit/test_order_repository_contract.py`).

## Code de conduite
En participant, vous acceptez le [code de conduite](CODE_OF_CONDUCT.md).
