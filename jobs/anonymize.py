"""Anonymisation RGPD des feedbacks.

Règles :
- J+180 après date_fin de la session : stagiaire_email remplacé par SHA-256 tronqué
- J+30  après date_saisie            : commentaire purgé (mis à NULL)

Exécutable en CRON :
    uv run python -m jobs.anonymize
"""

from __future__ import annotations

import hashlib
from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from collect._common import db_session, log


def anonymize_emails(session) -> int:
    """Remplace stagiaire_email par un hash SHA-256 tronqué (16 chars) pour les
    feedbacks dont la session s'est terminée il y a plus de 180 jours."""
    cutoff = date.today() - timedelta(days=180)
    rows = session.execute(
        text(
            """
            SELECT f.id, f.stagiaire_email
            FROM feedbacks f
            JOIN sessions s ON s.id = f.session_id
            WHERE s.date_fin < :cutoff
              AND f.stagiaire_email IS NOT NULL
              AND f.stagiaire_email NOT LIKE 'sha256:%'
            """
        ),
        {"cutoff": cutoff},
    ).fetchall()

    for row in rows:
        hashed = "sha256:" + hashlib.sha256(row.stagiaire_email.encode()).hexdigest()[:16]
        try:
            with session.begin_nested():
                session.execute(
                    text("UPDATE feedbacks SET stagiaire_email = :h WHERE id = :id"),
                    {"h": hashed, "id": row.id},
                )
        except IntegrityError:
            log.warning("jobs.anonymize.hash_collision", id=row.id, hash=hashed)

    log.info("jobs.anonymize.emails_done", count=len(rows))
    return len(rows)


def purge_comments(session) -> int:
    """Purge les commentaires saisis il y a plus de 30 jours (mis à NULL)."""
    cutoff = date.today() - timedelta(days=30)
    result = session.execute(
        text(
            """
            UPDATE feedbacks
            SET commentaire = NULL
            WHERE date_saisie < :cutoff
              AND commentaire IS NOT NULL
            """
        ),
        {"cutoff": cutoff},
    )
    nb = result.rowcount or 0
    log.info("jobs.anonymize.comments_done", count=nb)
    return nb


def run() -> None:
    log.info("jobs.anonymize.start")
    with db_session() as session:
        nb_emails = anonymize_emails(session)
        nb_comments = purge_comments(session)
    log.info(
        "jobs.anonymize.done",
        emails_anonymized=nb_emails,
        comments_purged=nb_comments,
    )


if __name__ == "__main__":
    run()
