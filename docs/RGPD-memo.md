# Mémo interne Nodalys — Données personnelles & RGPD
*Ce qu'on a le droit de collecter, ce qu'on n'a pas le droit de collecter*

**Diffusion :** équipe data + équipe produit
**Auteur :** DPO Nodalys
**Dernière mise à jour :** janvier 2025

---

## Rappel rapide du cadre légal

Notre SaaS B2B traite des données de stagiaires, de salariés d'organismes
clients et de formateurs. À ce titre, le **RGPD** (règlement UE 2016/679)
s'applique pleinement. Trois principes guident toutes nos collectes :

1. **Finalité explicite** : on collecte une donnée parce qu'elle sert un
   traitement défini contractuellement (gestion de session, suivi
   d'assiduité, facturation, etc.). Pas « au cas où ».
2. **Minimisation** : on ne collecte **que ce qui est strictement
   nécessaire** à cette finalité.
3. **Durée limitée** : on conserve les données le temps de la finalité +
   la durée légale de prescription (5 ans pour la facturation, 6 mois
   après la fin de session pour les feedbacks anonymisés).

## Champs autorisés

| Champ | Source | Finalité | Conservation |
|---|---|---|---|
| `prenom`, `nom` | API Nodalys (stagiaires) | Émargement, attestation | Durée de la session + 5 ans |
| `email` | API Nodalys (stagiaires) | Convocations, envoi attestation | Durée de la session + 5 ans **uniquement si le stagiaire est rattaché à une session active**. Sinon : ne pas stocker. |
| `session_id`, dates, code formation | API Nodalys (sessions) | Catalogue, planning | 5 ans après la fin de session |
| `commentaire feedback` | CSV exports | Amélioration continue | 6 mois après la fin de session, puis anonymisation |

## Champs **interdits** à la collecte

> Les champs ci-dessous sont parfois présents dans les réponses de nos
> APIs (héritage historique). Nos collecteurs **ne doivent pas** les
> stocker en base. Si tu en vois passer dans un script de collecte,
> c'est un bug à corriger.

| Champ | Raison |
|---|---|
| `telephone_personnel` | Non nécessaire à la finalité « formation ». Le contact passe par l'email professionnel ou via l'organisme. **À filtrer côté collecteur, même si l'API le renvoie.** |
| Date de naissance complète | Non nécessaire. Si un âge moyen est requis, utiliser l'année seule. |
| Adresse personnelle | Non nécessaire. L'adresse de facturation est portée par le `client` (l'organisme), pas par le stagiaire. |
| Numéro de sécurité sociale | Strictement interdit dans toute notre chaîne. |

## Cas particulier — feedbacks anonymisés

À J+180 après la fin de session, les feedbacks doivent être anonymisés :
le champ `stagiaire_email` est remplacé par un hash SHA-256 tronqué. Un
job d'anonymisation doit être prévu en CRON ; à date, rien n'est en
place côté pipeline.

Concerne aussi `commentaire` : tout commentaire libre est à tronquer ou
purger au bout de 30 jours s'il contient des informations susceptibles
de ré-identifier le stagiaire (mentions de manager, de prénoms tiers,
etc.). Pas non plus de job en place.

## Si tu as un doute

Demande au DPO. Ne devine jamais « ça doit aller, c'est juste pour le
debug ». Un log applicatif est aussi une collecte au sens RGPD.
