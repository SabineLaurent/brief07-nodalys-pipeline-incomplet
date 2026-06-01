include .env

.PHONY: up down migrate seed ingest anonymize chat test fmt logs dbreset dbcheck

up:
	docker compose up -d
	@echo "Postgres : localhost:5432 — Mock API : http://localhost:8001/docs"

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	uv run alembic upgrade head

seed:
	uv run python seed.py

ingest:
	uv run python -m collect.sessions
	uv run python -m collect.feedbacks

anonymize:
	uv run python -m collect.anonymize

chat:
	uv run python scripts/chat.py

test:
	uv run pytest -v

fmt:
	uv run ruff format . || true

dbreset:
	make down
	docker volume rm brief07-nodalys-pipeline-incomplet_nodalys_db_data
	make up

dbcheck:
	docker exec -i $(DB_CONTAINER) psql -U $(DB_USER) -d $(DB_NAME) < tests/queries-db-creation-control-test.sql
