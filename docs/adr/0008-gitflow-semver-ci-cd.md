# ADR-0008 — GitFlow, Semantic Versioning et CI/CD (GitHub Actions + ghcr.io)

- **Statut** : Accepté
- **Date** : 26/10/2026

## Contexte
Le projet passe sur GitHub. Il faut organiser les branches, numéroter les versions, tester
automatiquement chaque modification et livrer une image Docker reproductible.

## Options considérées
| Option | Avantages | Inconvénients |
|---|---|---|
| A. Une seule branche `main` | Simple | Pas de séparation entre ce qui est en cours et ce qui est livré |
| B. GitHub Flow (`main` + branches courtes) | Léger | Pas de branche de stabilisation des versions |
| C. GitFlow (`main`, `develop`, `feature/*`, `release/*`, `hotfix/*`) | Version livrée toujours sur `main`, correctifs à chaud possibles | Plus de branches à gérer |

## Décision
- **GitFlow** : `main` ne contient que des versions livrées et taguées ; `develop` intègre les
  `feature/*` via Pull Request ; une `release/X.Y.Z` stabilise une version puis est fusionnée
  dans `main` (tag `vX.Y.Z`) et dans `develop` ; `hotfix/*` part de `main`.
- **Semantic Versioning** `X.Y.Z` (majeur non rétrocompatible / mineur / correctif) pour
  l'application, l'image Docker et le modèle ; journal des modifications au format
  **Keep a Changelog** (`CHANGELOG.md`).
- **CI** (`.github/workflows/ci.yml`) sur chaque push GitFlow et chaque PR : ruff, pytest
  (dont l'intégration avec un service MongoDB), build de l'image de test et de production,
  smoke test (utilisateur non-root, `/health`).
- **CD** (`.github/workflows/release.yml`) : à chaque tag `vX.Y.Z`, build multi-stage et
  publication sur **ghcr.io** (`X.Y.Z`, `X.Y`, `latest`, `sha`) avec le `GITHUB_TOKEN` ; un
  push sur `develop` publie le tag `develop` (version de développement).

## Conséquences
- Une image en production correspond toujours à un tag Git : on sait exactement quels
  commits elle contient (label OCI `revision`).
- Protéger `main` et `develop` sur GitHub : PR obligatoire et CI verte avant fusion.
- Le registre est rattaché au compte propriétaire du dépôt, pas au dépôt lui-même.
