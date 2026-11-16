## Objet
<!-- Ce que change cette PR et pourquoi. Lien vers l'issue : Closes #… -->

## Type
- [ ] feature (branche `feature/*` -> `develop`)
- [ ] fix / hotfix (branche `hotfix/*` -> `main` et `develop`)
- [ ] release (branche `release/*` -> `main`)
- [ ] documentation / ADR

## Vérifications
- [ ] `ruff check .` et `ruff format --check .` passent
- [ ] `pytest` passe (tests ajoutés pour le nouveau comportement)
- [ ] `CHANGELOG.md` mis à jour (section `[Unreleased]`)
- [ ] ADR rédigé si une décision d'architecture est prise
- [ ] Aucun secret ni `.env` dans le diff
