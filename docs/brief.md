## Contexte du projet

Vous êtes développeur·se IA junior chez Nodalys. Un·e collègue avait commencé à remplacer l'export manuel de l'assistant par un vrai pipeline de collecte, mais il/elle a quitté l'entreprise en laissant le chantier à moitié fait : une source n'est pas collectée, une requête SQL ne renvoie rien, la base a une table manquante et l'assistant n'est plus branché sur les données.

La CTO vous demande de reprendre ce pipeline existant et de le compléter pour qu'il tourne de bout en bout, en respectant les conventions déjà posées par votre prédécesseur·e. L'objectif n'est pas de tout réécrire, mais de comprendre l'existant et de combler les trous sans casser ce qui marche.
Modalités pédagogiques

## Travail préliminaire de conception

À mener et faire valider par le formateur avant de modifier le code. À documenter dans une note de diagnostic (1 page).

Questions pour guider votre réflexion :

Comment le pipeline existant est-il organisé ? Quelles sont ses grandes étapes et dans quel ordre s'enchaînent-elles ?
Qu'est-ce qui fonctionne déjà et qu'il ne faut surtout pas casser ?
Qu'est-ce qui manque ou est cassé ? Comment l'avez-vous repéré (exécution, lecture du code, messages d'erreur) ?
Quelles conventions votre prédécesseur·e a-t-il/elle posées (nommage, formats, structure des fichiers) et que vous devez respecter pour rester cohérent·e ?
Y a-t-il des données personnelles collectées à tort dans l'existant, au regard du mémo RGPD ?

## Architecture / schéma attendus

Le schéma du flux existant annoté : pour chaque étape, marquer OK / manquant / cassé.
Vos tâches sont les suivantes :

- établir la note de diagnostic et le schéma annoté issus du travail préliminaire.
- compléter le script de collecte pour la source manquante, en imitant le pattern du script existant (C1).
- corriger / compléter la requête SQL défaillante à partir des exemples déjà présents dans le repo (C2).
- ajouter la table manquante au schéma de base en suivant la convention déjà en place (C4).
- rebrancher l'assistant Nodalys sur la base pour qu'il réponde de nouveau (C10).

## Modalités d'évaluation

- Validation de la note d'audit et du schéma annoté par le formateur (porte d'entrée du brief).
- Revue de code en 1:1 
- Point de passage final : démonstration d'une exécution complète du pipeline restauré.

## Livrables

- Une note d'audit (1 page) avec le schéma de flux annoté.
- Le repo complété : script de collecte, requêtes SQL, schéma de base, assistant rebranché.
- Un récapitulatif des modifications (ce qui manquait / était cassé → ce qui a été corrigé).

## Critères de performance

- Le pipeline tourne end-to-end après vos modifications, sans régression sur ce qui fonctionnait.
- Vos ajouts respectent les conventions de l'existant (nommage, formats).
- Aucune donnée personnelle non justifiée n'est collectée.
- Le journal des modifications permet à l'équipe de comprendre ce qui a changé.