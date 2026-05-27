# nodalys-pipeline-incomplet

Pipeline interne de collecte de données pour l'assistant Nodalys :
récupère sessions, stagiaires, contrats et feedbacks depuis l'API
web Nodalys et les fichiers métier, puis met le tout à disposition d'un
agent LangChain (LLM Kimi-K2.6 hébergé sur Azure AI Foundry).

## Stack

- Python 3.11+ — gestion d'env avec [uv](https://docs.astral.sh/uv/)
- PostgreSQL 16 (via Docker Compose)
- SQLAlchemy 2 + Alembic
- LangChain 1.x + `langchain-azure-ai`
- httpx + tenacity (collecte HTTP)
- pandas + pydantic (validation CSV)
- structlog (logging structuré)
- FastAPI (mock de l'API Nodalys, embarqué le temps que la prod soit
  ouverte aux flux entrants)

## Setup

```bash
cp .env.example .env       # renseigne AZURE_AI_INFERENCE_*
uv sync
make up                    # postgres + mock API en local
make migrate               # alembic upgrade head
make seed                  # contrats (fixtures)
make ingest                # collecte sessions + stagiaires + feedbacks
make chat                  # REPL avec l'assistant
```

Variables d'environnement (cf. `.env.example`) :

| Variable | Description |
|---|---|
| `DB_URL` | Chaîne SQLAlchemy vers Postgres |
| `NODALYS_API_BASE_URL` | URL du service web Nodalys (mock local par défaut) |
| `AZURE_AI_INFERENCE_ENDPOINT` | Endpoint Azure AI Inference |
| `AZURE_AI_INFERENCE_API_KEY` | Clé Azure AI Inference |
| `AZURE_AI_INFERENCE_MODEL` | Nom du déploiement (défaut `Kimi-K2.6`) |

## Layout

```
.
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── alembic.ini
├── mock_api/                         FastAPI — simule l'API Nodalys
├── migrations/versions/              Schéma Alembic
├── collect/                          Collecteurs (sessions, feedbacks…)
├── queries/                          Requêtes SQL exposées à l'assistant
├── assistant/                        Agent LangChain + outils
├── data/
│   ├── feedbacks/                    CSV exports trimestriels
│   └── contrats.json                 Fixtures contrats
├── docs/RGPD-memo.md                 Mémo DPO
└── scripts/                          Scripts ponctuels
```

## Known issues

Quelques points en suspens à reprendre :

- L'ingestion des feedbacks CSV n'est pas branchée.
- Plusieurs requêtes dans `queries/` sont des tentatives non
  finalisées (`contrats_actifs.sql`, `stagiaires_par_session.sql`,
  `feedbacks_recents.sql`).
- Schéma `contrats` : index préparé mais pas la table associée.
- Assistant : `query_feedbacks` n'est plus branché depuis le refactor
  du module `tools`.

## Contact

Reprise du projet : équipe data Nodalys. Tickets internes : Jira
`NODA-*`.
