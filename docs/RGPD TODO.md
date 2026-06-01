# Mémo interne Nodalys — Données personnelles & RGPD TODO

1. **Durée limitée** : on conserve les données le temps de la finalité +
   la durée légale de prescription (5 ans pour la facturation, 6 mois
   après la fin de session pour les feedbacks anonymisés).

2. À J+180 après la fin de session, les feedbacks doivent être anonymisés :
le champ `stagiaire_email` est remplacé par un hash SHA-256 tronqué. Un
job d'anonymisation doit être prévu en CRON ; à date, rien n'est en
place côté pipeline.

3. Concerne aussi `commentaire` : tout commentaire libre est à tronquer ou
purger au bout de 30 jours s'il contient des informations susceptibles
de ré-identifier le stagiaire (mentions de manager, de prénoms tiers,
etc.). Pas non plus de job en place.
