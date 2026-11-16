# ADR-0005 — Intégrer les données depuis MongoDB plutôt que PostgreSQL

- **Statut** : Accepté
- **Date** : 29/10/2026

## Contexte
L'application doit s'entraîner et prédire sur les commandes réelles de l'ERP « Pro 2015 ».
Deux bases sont disponibles :

```
ERP Pro 2015 ⇄ (bilatéral, temps réel) PostgreSQL ── ETL (unilatéral, temps réel) ──▶ MongoDB
              base de production                                                  base analytique
```

| | PostgreSQL | MongoDB |
|---|---|---|
| Rôle | Base de **production** de l'ERP | Base **analytique**, créée pour les Data Analysts |
| Historique | Depuis 2015 | Depuis 2023 seulement |
| Schéma | Modifié en 2017 et 2023 : `weekend` NULL avant 07/2015, `preparation_time_min` NULL avant 07/2017 | Documents complets depuis 2023 |
| Usage partagé | Aussi utilisée par **une autre application critique** | Dédiée à la Data |
| Maintenance | Non mise à jour depuis 2023, administrateur parti et non remplacé | Maintenue par un alternant bientôt en fin de contrat |
| Accès | `livraison` / `livraison`, table `public.orders` | Sans authentification, collection `orders` |

## Options considérées
| Option | Avantages | Inconvénients |
|---|---|---|
| A. PostgreSQL | Historique complet depuis 2015 (plus de données) | Lire la base de production fait peser nos requêtes d'entraînement (lecture complète de la table) sur l'ERP et sur l'application critique ; schéma hétérogène dans le temps ; plus aucun administrateur pour arbitrer un incident ; un bug ou un mauvais identifiant peut altérer les données de production |
| B. MongoDB | Conçue pour les usages Data : aucun impact sur la production ; flux ETL unilatéral (nos erreurs ne remontent jamais vers l'ERP) ; données récentes et homogènes, donc plus représentatives du comportement actuel | Historique plus court (2023+) ; pas d'authentification ; maintenance fragile (départ de l'alternant) ; latence de l'ETL |

## Décision
**Option B : MongoDB, base analytique.**

La règle de bonne pratique vue en cours prime : les traitements Data ne s'exécutent jamais
sur la base de production. L'historique 2023+ (des milliers de commandes, puis le flux
quotidien) est suffisant pour une régression logistique à 12 variables, et il reflète mieux
les conditions actuelles que des commandes de 2015 dont le schéma a changé deux fois.

Mise en œuvre (`infrastructure/implementation/mongo/`) :
- `MongoOrderRepository` implémente le contrat `OrderRepository` (une seule implémentation à
  écrire grâce à l'abstraction) ;
- la collection `orders` (alimentée par l'ETL) est ouverte **en lecture seule** pour
  l'entraînement ;
- les commandes reçues par `POST /v1/orders` sont écrites dans une collection distincte,
  `api_orders`, pour ne jamais mélanger nos écritures aux données de référence ;
- la sélection se fait par configuration : `ORDER_REPOSITORY_URL=mongodb://…`.

## Conséquences
- **Risques acceptés et mitigations :**
  - *absence d'authentification* → activée en production avec des comptes à moindre
    privilège ([ADR-0004](0004-securite-entrees-sorties-et-donnees.md), `mongo-init.js`) ;
  - *départ de l'alternant* → l'ETL et la base sont décrits en code (compose, scripts) et
    documentés ; un transfert de compétences est demandé avant la fin de son contrat ;
  - *historique court* → si le modèle manque de données, un import ponctuel et contrôlé de
    l'historique 2015-2022 depuis une **réplique** de PostgreSQL (jamais la production) pourra
    être ajouté (nouvelle ADR).
- Les données de l'ERP utilisent un autre vocabulaire et ne contiennent pas la cible : voir
  [ADR-0006](0006-contrat-de-donnees-et-etiquetage.md).
