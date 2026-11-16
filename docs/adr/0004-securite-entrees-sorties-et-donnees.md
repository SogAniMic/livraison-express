# ADR-0004 — Sécuriser les entrées/sorties et l'accès à la donnée

- **Statut** : Accepté
- **Date** : 09/10/2026

## Contexte
L'API manipule des données de commandes clients et un modèle qui constitue une propriété
intellectuelle. Les menaces : accès non autorisé, abus (déni de service), fuite de secrets,
compromission d'un conteneur, altération des données de référence.

## Options considérées
| Option | Avantages | Inconvénients |
|---|---|---|
| A. Sécurité dans l'application (auth, quotas dans FastAPI) | Autonome | Logique de sécurité dupliquée dans chaque service |
| B. Sécurité en périphérie (pare-feu + reverse proxy / API gateway) + moindre privilège | Centralisé, éprouvé, l'application reste simple | Un composant de plus à configurer |

## Décision
**Option B**, en défense en profondeur :

**Entrées / sorties**
1. *Pare-feu* : seuls les ports 443 (HTTPS) et 22 (SSH, restreint aux IP de l'équipe, par clé)
   sont ouverts. MongoDB n'est jamais exposé (aucun `ports:` dans `docker-compose.prod.yml`),
   l'API n'écoute que sur `127.0.0.1`.
2. *Reverse proxy / API gateway* : TLS, **clé d'API par application cliente** (expiration à
   90 jours, rotation avant expiration), **rate limiting** par clé, liste blanche d'IP internes.
3. *Validation stricte des entrées* : schéma OpenAPI appliqué par pydantic
   (`extra="forbid"`, bornes, énumérations) ; toute variable absente ou en trop → 422.
4. *Pas de fuite technique* : les erreurs renvoyées suivent le schéma `Error` ; les traces
   restent dans les logs. Aucun endpoint d'entraînement n'est exposé.

**Accès à la donnée**
5. *Moindre privilège* (`erp/docker/mongo-init.js`) : l'application ne peut que **lire** la
   collection `orders` et écrire dans `api_orders` ; seul l'ETL écrit dans `orders`.
6. *Secrets* : jamais dans Git ni dans l'image (`.gitignore`, `.dockerignore`) ; injectés en
   variables d'environnement depuis un gestionnaire de secrets ; l'URL de connexion est un
   `SecretStr` (jamais journalisée).
7. *Conteneurs* : non-root (UID 10001), système de fichiers en lecture seule,
   `cap_drop: ALL`, `no-new-privileges`, limites CPU/mémoire.
8. *Dépendances* : versions figées (`requirements.txt`), mises à jour suivies (Dependabot).

## Conséquences
- L'authentification par clé d'API est portée par la gateway : l'application doit rester
  inaccessible autrement que par elle (garanti par le réseau Docker et le pare-feu).
- Les rôles `admin` / `user` / `guest` sont gérés au niveau de la gateway.
- Une revue par un expert cybersécurité est requise avant la première mise en production.
