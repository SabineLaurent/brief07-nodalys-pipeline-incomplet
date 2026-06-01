# nodalys-pipeline-incomplet

Pipeline interne de collecte de données pour l'assistant Nodalys :
récupère sessions, stagiaires et feedbacks depuis l'API web Nodalys
et les fichiers CSV métier, charge les contrats depuis une fixture JSON,
puis met le tout à disposition d'un agent LangChain (LLM Kimi-K2.6
hébergé sur Azure AI Foundry).

## Stack

- Python 3.11+ — gestion d'env avec [uv](https://docs.astral.sh/uv/)
- PostgreSQL 16 (via Docker Compose)
- SQLAlchemy 2 + Alembic
- LangChain `>=1.0,<2.0` + `langchain-azure-ai` + `azure-ai-inference`
- httpx + tenacity (collecte HTTP — retry exponentiel + gestion 429)
- pydantic v2 (validation des payloads API et des lignes CSV)
- structlog (logging structuré)
- FastAPI (mock de l'API Nodalys, embarqué le temps que la prod soit
  ouverte aux flux entrants)

## Setup

```bash
cp .env.example .env       # renseigne AZURE_AI_INFERENCE_* et DB_*
uv sync
make up                    # postgres + mock API en local
make migrate               # alembic upgrade head
make ingest                # collecte sessions + stagiaires + feedbacks
make seed                  # contrats (fixture JSON)
make chat                  # REPL avec l'assistant
```

Variables d'environnement (cf. `.env.example`) :

| Variable | Description |
|---|---|
| `DB_URL` | Chaîne SQLAlchemy vers Postgres |
| `DB_USER` | Utilisateur Postgres (utilisé par `make dbcheck`) |
| `DB_NAME` | Nom de la base (utilisé par `make dbcheck`) |
| `DB_CONTAINER` | Nom du conteneur Docker Postgres (utilisé par `make dbcheck`) |
| `NODALYS_API_BASE_URL` | URL du service web Nodalys (défaut : `http://localhost:8001`) |
| `AZURE_AI_INFERENCE_ENDPOINT` | Endpoint Azure AI Inference |
| `AZURE_AI_INFERENCE_API_KEY` | Clé Azure AI Inference |
| `AZURE_AI_INFERENCE_MODEL` | Nom du déploiement (défaut : `Kimi-K2.6`) |

## Layout

```
.
├── docker-compose.yml             Postgres 16 + mock API
├── Makefile
├── pyproject.toml
├── alembic.ini
├── seed.py                        Charge data/contrats.json → table contrats
├── mock_api/                      FastAPI — simule l'API Nodalys
│   └── app/
│       ├── main.py                GET /health, /api/sessions, /api/stagiaires (cursor)
│       └── seed.py                Données fictives déterministes (seed=42)
├── migrations/versions/           Schéma Alembic (001→005)
│   ├── 001_create_sessions_and_clients.py
│   ├── 002_create_stagiaires.py
│   ├── 003_create_feedbacks.py
│   ├── 004_add_contracts.py
│   └── 005_add_contrats_index.py
├── collect/
│   ├── _common.py                 db_session, http_get_json (retry + 429), log
│   ├── sessions.py                API → clients + sessions + stagiaires (pagination cursor)
│   └── feedbacks.py               CSV → feedbacks (validation pydantic ligne par ligne)
├── queries/                       Fichiers SQL consommés par l'outil query_db
│   ├── top_formations.sql         Sessions Q3 par nb de stagiaires — fonctionnel
│   ├── stagiaires_par_session.sql Effectifs par session avec client — fonctionnel
│   ├── contrats_actifs.sql        Contrats actifs liés aux stagiaires par session
│   └── feedbacks_recents.sql      Feedbacks récents (filtre sur created_at)
├── assistant/
│   ├── tools.py                   @tool query_db + @tool query_feedbacks
│   └── agent.py                   Agent LangChain + Kimi-K2.6 (Azure)
├── data/
│   ├── feedbacks/                 CSV exports trimestriels (2024 T3 → 2025 T3)
│   └── contrats.json              Fixture contrats
├── docs/
│   ├── brief.md                   Énoncé du brief pédagogique
│   └── RGPD-memo.md               Mémo DPO — champs autorisés / interdits
├── scripts/
│   ├── chat.py                    REPL utilisateur (boucle question/réponse)
│   ├── generate_csv_feedbacks.py  Générateur de CSV de test
│   └── generate_contrats_fixture.py
└── tests/
    ├── test_smoke.py              Tests fumigènes minimes
    └── queries-db-creation-control-test.sql
```

## Schéma de base

```
clients ──< sessions ──< stagiaires
   │             │
   └───< contrats┘

sessions ──< feedbacks
```

| Table | Clé naturelle / contrainte notable |
|---|---|
| `clients` | `siret` UNIQUE |
| `sessions` | `code` UNIQUE |
| `stagiaires` | FK `session_id` |
| `feedbacks` | UNIQUE (`session_id`, `stagiaire_email`, `date_saisie`) |
| `contrats` | FK `client_id` + `session_id` ; index sur `(statut, date_signature)` |

## Points d'attention

### Bugs connus dans le code actuel

- **`assistant/agent.py`** — importe `create_agent` depuis `langchain.agents`,
  fonction qui n'existe pas dans LangChain ≥ 1.0. L'agent ne peut pas
  être instancié en l'état ; il faudra probablement `create_react_agent`
  ou équivalent selon la version cible.

- **`queries/feedbacks_recents.sql`** — filtre sur `f.created_at`
  (horodatage d'insertion en base) et non sur `f.date_saisie`
  (date de saisie du feedback). Si l'ingest n'a pas tourné dans les
  7 derniers jours, la requête renvoie zéro résultat même avec des
  feedbacks récents.

- **`queries/contrats_actifs.sql`** — joint `contrats` à `stagiaires`
  via `session_id`. Un contrat lie un client à une session, pas
  directement un stagiaire : la sémantique de la requête est discutable
  et peut produire des doublons par stagiaire.

### RGPD

- La mock API expose `telephone_personnel` dans `/api/stagiaires`
  (champ interdit à la collecte selon `docs/RGPD-memo.md`). Le
  collecteur `collect/sessions.py` ne stocke pas ce champ (la table
  `stagiaires` ne le contient pas), mais aucune assertion explicite ne
  l'écarte au niveau du collecteur.
- Aucun job d'anonymisation des feedbacks n'est implémenté
  (`stagiaire_email` + `commentaire` à anonymiser à J+180 selon le mémo).

## Contact

Reprise du projet : équipe data Nodalys. Tickets internes : Jira `NODA-*`.
