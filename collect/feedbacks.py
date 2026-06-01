"""Collecteur — feedbacks de fin de session (CSV).

Source : fichiers CSV dans ``data/feedbacks/*.csv``.
Cible  : table ``feedbacks``.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import text

from collect._common import db_session, log


class FeedbackRow(BaseModel):
    """Schéma d'une ligne de feedback telle que lue dans les CSV."""
    session_id: int
    stagiaire_email: str | None = None
    date_saisie: date
    note_globale: int = Field(ge=1, le=5)
    commentaire: str | None = None
    source_csv: str


def list_csv_files() -> list[Path]:
    """Liste les chemins d'accès des fichiers CSV de feedbacks à traiter."""
    data_dir = Path(__file__).parent.parent / "data" / "feedbacks"
    files = sorted(data_dir.glob("*.csv"))
    log.info("collect.feedbacks.csv_found", count=len(files))
    return files


def read_csv(path: Path) -> list[FeedbackRow]:
    """Lit un fichier CSV et valide chaque ligne via pydantic."""
    rows = []
    skipped = 0
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for raw in reader:
            try:
                row = FeedbackRow.model_validate(
                    {**raw, "source_csv": path.name}
                )
                rows.append(row)
            except ValidationError as e:
                skipped += 1
                log.warning(
                    "collect.feedbacks.row_skipped",
                    file=path.name,
                    row=raw,
                    error=str(e),
                )
    log.info("collect.feedbacks.csv_read", file=path.name, count=len(rows), skipped=skipped)
    return rows


def upsert_feedbacks(session, rows: list[FeedbackRow]) -> int:
    """Upsert idempotent des feedbacks d'une session."""
    inserted = 0
    for row in rows:
        result = session.execute(
            text(
                """
                INSERT INTO feedbacks (
                    session_id, stagiaire_email, date_saisie,
                    note_globale, commentaire, source_csv
                )
                VALUES (
                    :session_id, :stagiaire_email, :date_saisie,
                    :note_globale, :commentaire, :source_csv
                )
                ON CONFLICT ON CONSTRAINT uq_feedbacks_session_email_date
                DO UPDATE SET
                    note_globale = EXCLUDED.note_globale,
                    commentaire  = EXCLUDED.commentaire,
                    source_csv   = EXCLUDED.source_csv
                """
            ),
            # Requete paramétrée avec les champs du modèle Pydantic --> évite les injections SQL.
            row.model_dump(),
        )
        inserted += result.rowcount or 0
    return inserted


def run() -> None:
    log.info("collect.feedbacks.start")
    csv_files = list_csv_files()
    total = 0
    with db_session() as session:
        for path in csv_files:
            rows = read_csv(path)
            nb = upsert_feedbacks(session, rows)
            total += nb
    log.info("collect.feedbacks.done", upserted=total)


if __name__ == "__main__":
    run()
