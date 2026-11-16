# ADR-0006 — Contrat de données ERP → modèle, et étiquetage provisoire

- **Statut** : Accepté
- **Date** : 29/10/2026

## Contexte
En branchant l'application sur MongoDB, trois écarts apparaissent entre les données de l'ERP
et le contrat du modèle (`docs/api/openapi.yml`, cellule 20 du notebook) :

| Champ | ERP (MongoDB) | Modèle / API |
|---|---|---|
| `weather` | `clear`, `rain`, `wind`, `snow` | `normal`, `pluie`, `neige`, `orage` |
| `delivery_zone` | `centre`, `suburb`, `rural` | `centre`, `proche_banlieue`, `banlieue`, `rurale` |
| `customer_type` | `individual`, `business` | `standard`, `premium` |
| `carrier_capacity` | nombre de véhicules (5 à 50) | taux de capacité (0 à 1) |
| `express_eligible` | **absente** | cible de l'entraînement |

Faire confiance à la qualité des données serait une erreur : il faut valider et nettoyer.

## Options considérées
| Option | Avantages | Inconvénients |
|---|---|---|
| A. Réentraîner sur le vocabulaire brut de l'ERP | Pas de traduction | API et entraînement divergent ; contrat OpenAPI cassé pour les clients |
| B. Couche anti-corruption à l'entrée de l'application (validation + traduction) | Contrat unique, erreurs isolées et comptées | Hypothèses de correspondance à valider avec le métier |
| C. Corriger les données dans MongoDB | Données propres pour tous | Interdit : l'application ne doit pas modifier la base de référence |

Pour la cible absente :

| Option | Avantages | Inconvénients |
|---|---|---|
| D. Attendre le retour terrain (livrée / non livrée dans la journée) | Vraie vérité terrain | Bloque le projet ; donnée non disponible aujourd'hui |
| E. Étiqueter par la règle métier du notebook (supervision faible) | Débloque l'industrialisation de bout en bout | Le modèle apprend la règle, pas la réalité |

## Décision
**B + E.**

- `ErpOrderMapper` (`infrastructure/implementation/mongo/order_mappers.py`) valide chaque
  document (types, bornes, valeurs autorisées) et traduit le vocabulaire :
  `clear→normal`, `rain→pluie`, `snow→neige`, `wind→orage` (hypothèse : vent = intempérie la
  plus pénalisante), `suburb→banlieue`, `rural→rurale`, `individual→standard`,
  `business→premium` (hypothèse : contrat B2B = service prioritaire),
  `carrier_capacity / 50` borné à 1.
- Les colonnes migrées sont tolérées : `weekend` absent est dérivé de `day_of_week` ;
  `preparation_time_min` absent est imputé par la médiane dans la pipeline.
- Un document invalide est **écarté, compté et journalisé**, jamais propagé.
- `BusinessRuleLabeler` étiquette les commandes avec la règle de la cellule 8 du notebook
  (tirage de Bernoulli déterministe par `order_id` : reproductible).
- La limite est inscrite dans la *model card* (`limitations`), visible sur `GET /v1/model`.

## Conséquences
- Les hypothèses de correspondance (`wind`, `business`, capacité) sont à faire valider par
  l'expert métier ; elles sont toutes dans un seul fichier, testé (`tests/unit/test_erp_mapper.py`).
- Dès que la logistique fournit la vraie cible, `BusinessRuleLabeler` est remplacé par une
  jointure avec ce retour terrain, sans toucher au reste (abstraction `Labeler`), et cette
  ADR passe au statut « Superseded ».
