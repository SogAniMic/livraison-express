# ADR-0003 — Stratégie de déploiement

- **Statut** : Accepté
- **Date** : 09/10/2026

## Contexte
Une montée de version peut concerner le code (nouvelle image Docker) ou le modèle (nouveau
`.joblib`). Les utilisateurs de l'API sont des applications internes : une interruption bloque
la préparation des commandes express. Il faut pouvoir revenir en arrière en quelques secondes.

## Options considérées
| Option | Avantages | Inconvénients |
|---|---|---|
| Big Bang | Simple | Interruption, pas de retour arrière rapide |
| Déploiement pilote / Canary | Risque limité à une fraction du trafic | Il faut séparer les utilisateurs et comparer deux versions : outillage à construire |
| Blue / Green | Aucune interruption, rollback instantané (bascule du proxy) | Deux instances en parallèle pendant la bascule |
| Rolling | Progressif | Pertinent avec plusieurs instances (Kubernetes) |
| Shadow | Teste la nouvelle version sur le trafic réel sans impact | Double calcul, comparaison des réponses à outiller |

## Décision
- **Code applicatif : Blue / Green.** La nouvelle image (`green`) démarre à côté de l'ancienne
  (`blue`). Elle ne reçoit le trafic du reverse proxy que lorsque `GET /health/ready` répond
  200 (modèle chargé, base joignable). Après une période d'observation, `blue` est arrêtée ;
  en cas d'erreur, **rollback** en rebasculant le proxy sur `blue`.
- **Correctif urgent : Hotfix** (branche `hotfix/*` de GitFlow) puis même procédure.
- **Modèle** : remplacement à chaud par le scheduler, uniquement si l'entraînement réussit
  (les métriques sont consignées dans la model card). Le mode **Shadow** est retenu comme
  évolution pour comparer un nouveau modèle à l'ancien avant de le servir.

## Conséquences
- La sonde `/health/ready` est le critère de bascule : elle doit rester fiable (testée en CI).
- L'image est versionnée par SemVer : le rollback consiste à redéployer le tag précédent.
- Fenêtre de déploiement : hors heures d'activité (avant 7 h), communiquée aux équipes.
