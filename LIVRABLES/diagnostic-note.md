# Note de diagnostic

## Organisation du pipeline existant

Le pipeline est constitué de:

### Trois sources de données différentes

- API Nodalys (mocké en environnement de developpement);
- fichiers `data/feedbacks/*.csv`;
- fichier `data/contrats.json`.

### Une base de données sous serveur Postgres

C'est la BDD Nodalys, que l'agent IA va questionner.

### La logistique fonctionnelle sous forme de packages

Pour extraire la donnée des sources disctintes et enrichir la BDD.

## Pipeline: grandes étapes et ordre d'enchainement

Le pipeline est organisé en 4 grandes étapes:

### 1. Migration

La migration est initiée par la commande `make migrate`.
Cette étape va créer les tables en BDD.

### 2. Ingest

Le transfert de données est lancé par la commande `make ingest`.
Cette étape va permettre d'extraire les données nécessaires qui sont contenues dans l'API Nodalys (clients, sessions, stagiaires), ainsi que les informations de retour des stagiaires (feedbacks) stockées en fichiers .csv.

### 3. Seed

L'ajout des données de contrats se fait avec la commande `make seed`.

### 4. Chat

La commande `make chat` démarre le chat boosté à l'IA: l'Assistant Nodalys.

### Ordre à respecter

1. `make up` pour monter les conteneurs dockers de l'API Nodalys ainsi que celui de la BDD Nodalys qui est sur serveur Postgres. Cela se fait avec docker compose.
2. `make migrate` pour créer les tables en BDD Nodalys. Tables clients et sessions, puis stagiaires, puis feedbacks et enfin contrats. L'ordre de création des tables est imposé par les relations des tables entre elles. Une table A qui comporte une clé étrangère issue d'une table B, devra être créée après elle. Ainsi, la table B est créer en premier et ensuite la table A. Il en est de même pour l'ordre de remplissage de ses tables.
3. `make ingest` permet de remplir les tables clients, sessions et stagiaires avec les données appropriées.
4. `make seed` L'enregistrement en BDD des données de contrats se fait après le ingest car les données de contrats dépendent des tables clients et sessions.
5. `make chat` C'est une fois la BDD Nodalys complétée que le chat IA peut être démarré.

## Ce qui fonctionne

- docker compose (`make up`): monte l'API Nodalys (source) et lance le serveur Postgres, crée le user nodalys et la base de données nodalys.
- les migrations 001, 002, 003.
- la collecte de la source session.py (sessions + clients + stagiaires)
- l'agent est bien composé d'un LLM et de tools

## Ce qui est cassé

- le `make migrate` casse après la 3e étape de migration.
  - Le fichier correspondant à l'étape 004 est manquant. Pour me permettre d'avoir une meilleur visibilité du flux des données, j'ai créé le fichier sur la même base que ceux fonctionnels mais avec les fonctions `upgrade()` et `downgrade()` vides et contenant `pass` –> passage direct à l'étape suivante.
  - L'étape 005 est dépendante de l'étape 004 car elle crée les index pour la table `contrats`. L'étape 004 est donc celle qui crée le modèle contrat en BDD. Comme précédemment, pour avancer et avoir une vue globale du pipeline, j'ai commenté le contenu des fonctions et utilisé `pass` pour passer à la suite, dans un premier temps.

- le `make ingest` casse. Le script `collect/feedbacks.py` a été laissé en stand by et est à coder.

- le `make chat` génère une erreur. La variable d'environnement utilisée dans query_feedbacks() n'est pas présente dans le .env du projet.
  
- le tool `query_feedbacks` de l'agent n'est pas branché dans `agent.py` (fonction `build_agent()`)

- les requettes SQL dans le dossier `queries/` sont à revoir.

## Conventions déjà en place et à respecter

- nommage des fonctions et variables en anglais
- snake_case
- nom de fonction explicite avec verbe + nom
- desciption de fonction en docstrings et en français.

## Le mémo RGPD est-il respecté?

Il n'est pas respecté.

- En l'état, il n'y a pas de gestion de l'anonymisation des feedbacks 6 mois après la fin de session de formation, ni suppression des données 5 ans après la fin de formation.
- Le filtrage des numéros de téléphone des stagiaires n'est pas explicite lors de la récupération des data provenant de l'API mockée.
- Filtre du contenu nominatif des feedbacks après 30 jours à implémenter.

## Ce que j'ai modifié

cf. mon historique de commit
J'ai fait au mieux pour avoir des messages de commit explicitent et des push atomiques. J'espère que c'est le cas.

---

# Pour aller plus loin

Améliorations envisageables:
- export les logs d'erreur ingest dans un fichier de log dédié, pour vérification et modification manuel des données en anomalie.
- ajout d'une mémoire des échanges pour le session en cours.
- ajout de commandes du type /nom-de-la-commande pour interroger l'IA sur des questions récurrentes.
  