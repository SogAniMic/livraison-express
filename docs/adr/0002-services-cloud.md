# ADR-0002 — Quels services cloud ?

- **Statut** : Accepté
- **Date** : 09/10/2026

## Contexte
Suite à l'[ADR-0001](0001-plateforme-de-deploiement.md), il faut choisir les services cloud.
Le système comprend : une API stateless, un job de réentraînement, une base MongoDB, un
registre d'images Docker. La charge est faible ; le projet doit rester simple (KISS) et
réversible.

## Options considérées
| Option | Avantages | Inconvénients |
|---|---|---|
| A. Machine virtuelle (VPS) + Docker Compose | Simple, peu coûteux, identique à l'environnement de test, aucun verrouillage | Mise à l'échelle manuelle, OS à maintenir |
| B. Conteneurs managés (Cloud Run, Azure Container Apps, ECS Fargate) | Pas de serveur à gérer, auto-scaling | Verrouillage fournisseur, jobs planifiés et volumes partagés plus complexes |
| C. Kubernetes managé (GKE, AKS, EKS, Kapsule) | Standard, auto-scaling, rolling/blue-green natifs | Surdimensionné pour 3 conteneurs, compétences requises |
| D. Base MongoDB managée (Atlas) | Sauvegardes, haute disponibilité | Coût, données hors de notre infrastructure |

## Décision
- **Calcul : option A**, une VM dans une région UE (OVHcloud ou Scaleway, hébergeurs français)
  exécutant `docker-compose.prod.yml`.
- **Registre d'images : GitHub Container Registry (ghcr.io)**, alimenté par la CI
  ([ADR-0008](0008-gitflow-semver-ci-cd.md)).
- **Base de données** : MongoDB conteneurisé avec volume persistant et sauvegarde quotidienne
  (`mongodump`) vers un stockage objet ; Atlas (D) envisagé si la base devient critique.
- **Réseau** : un reverse proxy (Traefik ou nginx) termine le TLS devant l'API.

## Conséquences
- L'environnement de production est décrit en code, identique au test, à quelques réglages près.
- La mise à l'échelle est verticale (taille de la VM). Le passage à Kubernetes (option C) sera
  réévalué après la séance du 10/12/2026 ou si la charge dépasse une VM.
