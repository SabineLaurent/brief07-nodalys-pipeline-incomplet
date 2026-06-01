"""Purge RGPD des données de facturation après prescription légale (5 ans).

Règle :
- J+5ans après date_fin de la session : suppression en cascade
  feedbacks → stagiaires → contrats → sessions → clients orphelins

Exécutable en CRON :
    uv run python -m jobs.purge_billing
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import text

from collect._common import db_session, log


def purge_old_billing_data(session) -> dict[str, int]:
    """Supprime toutes les données de facturation dont la session s'est terminée
    il y a plus de 5 ans (prescription légale facturation — mémo RGPD §1).

    Ordre de suppression respectant les contraintes FK :
    feedbacks → stagiaires → contrats → sessions → clients orphelins.
    """
    today = date.today()
    cutoff = today.replace(year=today.year - 5)

    r_feedbacks = session.execute(
        text(
            """
            DELETE FROM feedbacks
            WHERE session_id IN (
                SELECT id FROM sessions WHERE date_fin < :cutoff
            )
            """
        ),
        {"cutoff": cutoff},
    )
    r_stagiaires = session.execute(
        text(
            """
            DELETE FROM stagiaires
            WHERE session_id IN (
                SELECT id FROM sessions WHERE date_fin < :cutoff
            )
            """
        ),
        {"cutoff": cutoff},
    )
    r_contrats = session.execute(
        text(
            """
            DELETE FROM contrats
            WHERE session_id IN (
                SELECT id FROM sessions WHERE date_fin < :cutoff
            )
            """
        ),
        {"cutoff": cutoff},
    )
    r_sessions = session.execute(
        text("DELETE FROM sessions WHERE date_fin < :cutoff"),
        {"cutoff": cutoff},
    )
    r_clients = session.execute(
        text(
            """
            DELETE FROM clients
            WHERE id NOT IN (SELECT DISTINCT client_id FROM sessions)
            """
        ),
    )

    counts = {
        "feedbacks": r_feedbacks.rowcount or 0,
        "stagiaires": r_stagiaires.rowcount or 0,
        "contrats": r_contrats.rowcount or 0,
        "sessions": r_sessions.rowcount or 0,
        "clients": r_clients.rowcount or 0,
    }
    log.info("jobs.purge_billing.done", **counts)
    return counts


def run() -> None:
    log.info("jobs.purge_billing.start")
    with db_session() as session:
        purge_old_billing_data(session)


if __name__ == "__main__":
    run()
