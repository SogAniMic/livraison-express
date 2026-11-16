# Politique de sécurité

## Versions maintenues
| Version | Maintenue | Fin de support |
|---|---|---|
| 1.0.x | ✅ | 6 mois après la sortie de 1.1.0 |
| < 1.0 | ❌ | — |

Seule la dernière version mineure reçoit des correctifs de sécurité.

## Signaler une vulnérabilité
**Ne créez pas d'issue publique.** Utilisez le signalement privé de GitHub
(onglet *Security* → *Report a vulnerability*) en précisant :
- la version concernée (`GET /health`) et le tag de l'image Docker ;
- les étapes de reproduction et l'impact estimé ;
- si possible, une proposition de correctif.

## Délais de traitement
| Étape | Délai |
|---|---|
| Accusé de réception | 72 h ouvrées |
| Évaluation de la criticité (CVSS) | 7 jours |
| Correctif — critique / haute | 7 jours (branche `hotfix/*`) |
| Correctif — moyenne / basse | prochaine version mineure |

Les vulnérabilités corrigées sont publiées dans un *Security Advisory* GitHub, avec un
identifiant CVE lorsque c'est pertinent, et mentionnées dans `CHANGELOG.md`.

## Mesures en place
Voir [ADR-0004](docs/adr/0004-securite-entrees-sorties-et-donnees.md) : conteneur non-root
en lecture seule, secrets hors de Git et de l'image, comptes MongoDB à moindre privilège,
validation stricte des entrées, dépendances figées et suivies par Dependabot.
