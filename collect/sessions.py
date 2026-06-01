"""Collecteur — sessions de formation Nodalys.

C'EST LE PATTERN DE RÉFÉRENCE de ce repo. Tout autre collecteur doit s'en
inspirer (nommage, structure, logging, upsert idempotent).

Source : API Nodalys, ``GET /api/sessions`` (mockée pour le développement).
Cible  : tables ``clients`` et ``sessions`` (Postgres).

Lancement :
    uv run python -m collect.sessions
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field
from sqlalchemy import text

from collect._common import (
    db_session,
    get_api_base_url,
    http_get_json,
    log,
)


class SessionPayload(BaseModel):
    """Schéma d'une session telle que la renvoie l'API Nodalys."""

    id: int
    code: str = Field(min_length=3, max_length=64)
    titre: str
    client_id: int
    client_raison_sociale: str
    date_debut: date
    date_fin: date
    duree_heures: int = Field(ge=1)
    places_max: int = Field(ge=1)


class StagiairePayload(BaseModel):
    """Schéma d'un stagiaire — liste blanche explicite des champs autorisés.

    telephone_personnel est délibérément absent : champ interdit par le mémo RGPD.
    Pydantic ignore structurellement tout champ non déclaré (extra='ignore' par défaut).
    """

    id: int
    session_id: int
    prenom: str
    nom: str
    email: str | None = None


def fetch_sessions() -> list[SessionPayload]:
    """Appelle l'API mock et valide la charge utile via pydantic."""
    base = get_api_base_url()
    payload = http_get_json(f"{base}/api/sessions")
    items = [SessionPayload.model_validate(item) for item in payload["items"]]
    log.info("collect.sessions.fetched", count=len(items))
    return items


def upsert_clients(session, sessions_payload: list[SessionPayload]) -> int:
    """Upsert idempotent des clients référencés par les sessions."""
    seen: dict[int, str] = {}
    for s in sessions_payload:
        seen[s.client_id] = s.client_raison_sociale
    inserted = 0
    for client_id, raison in seen.items():
        result = session.execute(
            text(
                """
                INSERT INTO clients (id, siret, raison_sociale)
                VALUES (:id, :siret, :raison)
                ON CONFLICT (id) DO UPDATE
                  SET raison_sociale = EXCLUDED.raison_sociale
                """
            ),
            {"id": client_id, "siret": f"FR{client_id:011d}", "raison": raison},
        )
        inserted += result.rowcount or 0
    return inserted


def upsert_sessions(session, sessions_payload: list[SessionPayload]) -> int:
    """Upsert idempotent — clé naturelle : ``id``."""
    inserted = 0
    for s in sessions_payload:
        result = session.execute(
            text(
                """
                INSERT INTO sessions (
                    id, code, titre, client_id, date_debut, date_fin,
                    duree_heures, places_max
                )
                VALUES (
                    :id, :code, :titre, :client_id, :date_debut, :date_fin,
                    :duree_heures, :places_max
                )
                ON CONFLICT (id) DO UPDATE
                  SET code = EXCLUDED.code,
                      titre = EXCLUDED.titre,
                      client_id = EXCLUDED.client_id,
                      date_debut = EXCLUDED.date_debut,
                      date_fin = EXCLUDED.date_fin,
                      duree_heures = EXCLUDED.duree_heures,
                      places_max = EXCLUDED.places_max
                """
            ),
            s.model_dump(exclude={"client_raison_sociale"}),
        )
        inserted += result.rowcount or 0
    return inserted


def upsert_stagiaires(session) -> int:
    """Collecte des stagiaires depuis ``GET /api/stagiaires`` et upsert."""
    base = get_api_base_url()
    inserted = 0

    # 1) Au lancement, on a une page complète sans curseur. Si l'API pagine, elle renverra un curseur pour la page suivante.
    cursor = None 
    while True:
        url = f"{base}/api/stagiaires"
        # Si on a un curseur, c'est qu'on n'est pas à la première page, donc on l'ajoute à l'URL pour récupérer la page suivante.
        if cursor:
            url += f"?cursor={cursor}"
        
        payload = http_get_json(url)
        for item in payload["items"]:
            result = session.execute(
                text(
                    """
                    INSERT INTO stagiaires (id, session_id, prenom, nom, email)
                    VALUES (:id, :session_id, :prenom, :nom, :email)
                    ON CONFLICT (id) DO UPDATE
                      SET session_id = EXCLUDED.session_id,
                          prenom = EXCLUDED.prenom,
                          nom = EXCLUDED.nom,
                          email = EXCLUDED.email
                    """
                ),
                {
                    "id": item["id"],
                    "session_id": item["session_id"],
                    "prenom": item["prenom"],
                    "nom": item["nom"],
                    "email": item["email"],
                },
            )
            inserted += result.rowcount or 0

        # 2) Si l'API renvoie un curseur, c'est qu'il y a une page suivante, et on le stocke pour la prochaine requête.
        cursor = payload.get("next_cursor")

        # 3) Si l'API ne renvoie pas de curseur, c'est qu'on a atteint la dernière page, et on sort de la boucle.
        if cursor is None:
            break

    log.info("collect.stagiaires.upserted", count=inserted)
    return inserted


def run() -> None:
    log.info("collect.sessions.start")
    sessions_payload = fetch_sessions()
    with db_session() as session:
        nb_clients = upsert_clients(session, sessions_payload)
        nb_sessions = upsert_sessions(session, sessions_payload)
        nb_stagiaires = upsert_stagiaires(session)
    log.info(
        "collect.sessions.done",
        clients=nb_clients,
        sessions=nb_sessions,
        stagiaires=nb_stagiaires,
    )


if __name__ == "__main__":
    run()
