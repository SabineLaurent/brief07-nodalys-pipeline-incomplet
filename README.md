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

Jobs RGPD (exécutés automatiquement par le service `cron` Docker) :

```bash
make anonymize             # anonymisation emails J+180, purge commentaires J+30
make purge-billing         # purge données facturation J+5ans
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
├── docker-compose.yml             Postgres 16 + mock API + service cron RGPD
├── Dockerfile.cron                Image du service cron (anonymize quotidien + purge billing mensuel)
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
├── jobs/                          Jobs planifiés — cycle de vie des données
│   ├── anonymize.py               CRON quotidien 2h00 — email SHA-256 J+180, purge commentaire J+30
│   └── purge_billing.py           CRON mensuel 1er du mois 3h00 — purge facturation J+5ans
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

## RGPD

| Règle | Implémentation |
|---|---|
| `telephone_personnel` interdit à la collecte | `StagiairePayload` Pydantic — champ structurellement absent |
| Email stocké seulement pour sessions actives | `upsert_stagiaires` conditionne l'email à `date_fin >= aujourd'hui` |
| `stagiaire_email` anonymisé à J+180 | `jobs/anonymize.py` — hash SHA-256 tronqué 16 chars, préfixe `sha256:` |
| `commentaire` purgé à J+30 | `jobs/anonymize.py` — mis à NULL |
| Données de facturation purgées à J+5ans | `jobs/purge_billing.py` — suppression en cascade feedbacks → stagiaires → contrats → sessions → clients orphelins |

## Points d'attention

### Re-ingest après anonymisation

Lorsque `jobs/anonymize.py` hash un `stagiaire_email`, la clé unique de la row passe de l'email original à `sha256:…`. Si `makeingest` est relancé après coup, le collecteur `collect/feedbacks.py` réinsère la ligne d'origine (email en clair) sans conflit de contrainte — la clé composite `(session_id, stagiaire_email, date_saisie)` est différente, créant un doublon en base. Au prochain run du cron, la tentative d'anonymiser ce doublon lève une `UniqueViolation` (deux rows pour le même hash sur le même `(session_id, date_saisie)`).
`jobs/anonymize.py` gère ce cas via un savepoint par ligne : la collision est loguée (`jobs.anonymize.hash_collision`) et la row en doublon est ignorée. La conformité RGPD n'est pas dégradée puisque la donnée en clair est en attente d'anonymisation au prochain cron.

La correction structurelle serait d'empêcher le collecteur de réinsérer des lignes pour des sessions déjà anonymisées.

### Filtre des feedbacks

Pour etre conforme au RGPD, une purge des feedbacks est faite après 30 jours. Faute de solution de filtre pérrenne pour le moment. A voir avec la mise en place d'un agent IA de filtre, peut etre.

## Contact

Reprise du projet : équipe data Nodalys. Tickets internes : Jira `NODA-*`.
