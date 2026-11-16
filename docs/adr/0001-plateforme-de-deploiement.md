# ADR-0001 — Plateforme de déploiement : cloud, on-premise ou local ?

- **Statut** : Accepté
- **Date** : 09/10/2026

## Contexte
Le livrable est une API HTTP de prédiction (FastAPI) et un job de réentraînement, consommés par
les applications internes (préparation de commandes, service client). Ce n'est ni une
application mobile (store), ni une application de bureau, ni un plugin : la plateforme est donc
un serveur. Contraintes :

- disponibilité en heures ouvrées étendues (7 h – 23 h, cf. variable `hour` des commandes) ;
- charge faible et prévisible (quelques milliers de prédictions par jour), pics ponctuels ;
- données de commandes clients : soumises au RGPD ;
- petite équipe Data, pas d'équipe d'exploitation dédiée à des serveurs physiques ;
- budget limité.

## Options considérées
| Option | Avantages | Inconvénients |
|---|---|---|
| A. Local (poste d'un développeur) | Gratuit, immédiat | Ni disponibilité, ni sécurité : exclu pour la production |
| B. On-premise (serveur de l'entreprise) | Données dans les murs, pas de coût récurrent | Achat, maintenance matérielle, sauvegardes, astreintes ; administrateur parti non remplacé |
| C. Cloud | Pas de matériel, scalabilité, sauvegardes et supervision fournies | Coût récurrent, dépendance au fournisseur, localisation des données à maîtriser |

## Décision
**Option C : cloud**, dans une région située dans l'Union européenne (France de préférence)
pour respecter le RGPD et la souveraineté des données clients. L'environnement local reste
utilisé uniquement pour le développement (`ORDER_REPOSITORY_URL=memory://`).

## Conséquences
- Les services précis sont choisis dans l'[ADR-0002](0002-services-cloud.md).
- Tout est conteneurisé (Docker) : l'application ne dépend pas d'un fournisseur et peut
  revenir on-premise si la politique de l'entreprise change.
- Les coûts sont suivis mensuellement ; cette décision est révisée si la facture dépasse
  celle d'un serveur on-premise amorti sur 3 ans.
