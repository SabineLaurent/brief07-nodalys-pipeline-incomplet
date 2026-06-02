# Journal des modifications

| Type | Problème / Issue | Correction | Fichier(s) |
|------|-----------------|------------|------------|
| feat | Pas de collecteur pour les feedbacks CSV | Collecteur complet : lecture CSV, validation Pydantic, upsert idempotent | `collect/feedbacks.py` |
| fix | Une ligne CSV invalide faisait crasher tout le collecteur | `ValidationError` catchée — ligne skippée avec `log.warning`, compteur `skipped` ajouté | `collect/feedbacks.py` |
| feat | Pipeline non exécutable sans configuration | `.env.example`, commandes Makefile, requêtes de contrôle | `.env.example`, `Makefile` |
| fix | `query_feedbacks()` utilisait `DB_FEEDBACK_URL` — variable inexistante | Remplacée par `DB_URL` + docstring ajoutée à `query_db()` | `assistant/tools.py` |
| fix | `contrats_actifs.sql` — JOIN sur `contrats.stagiaire_id` inexistant en base | JOIN réécrit via `contrats.session_id = stagiaires.session_id` | `queries/contrats_actifs.sql` |
| fix | `feedbacks_recents.sql` — littéral `'7 days'` rejeté par PostgreSQL (typage strict) | Remplacé par `INTERVAL '7 days'` | `queries/feedbacks_recents.sql` |
| fix | `stagiaires_par_session.sql` — alias `client` absent du `GROUP BY` → erreur PostgreSQL | `GROUP BY` étendu à `sessions.id, sessions.titre, client` | `queries/stagiaires_par_session.sql` |
| feat | Outil `query_feedback` absent de l'agent | Ajout de l'outil dans la liste des tools de l'agent | `assistant/agent.py` |
| feat | Collecteur sessions sans gestion de la pagination ni du rate limit 429 | Boucle curseur + lecture header `Retry-After` + `time.sleep()` | `collect/sessions.py` |
| fix | API renvoyait 429 sur les feedbacks sans être gérée → crash | Détection 429, `Retry-After` lu, pause avant retry dans `http_get_json()` | `collect/_common.py` |
| feat | RGPD 1 — `telephone_personnel` filtré par omission (fragile) | `StagiairePayload` Pydantic — champ absent structurellement | `collect/sessions.py` |
| feat | RGPD 2 — email stocké sans vérifier l'activité de la session | `fetch_stagiaires()` + `active_session_ids` — email conditionné à `date_fin >= aujourd'hui` | `collect/sessions.py` |
| feat | RGPD 3 — anonymisation des feedbacks complètement absente | Module CRON : hash SHA-256 email à J+180, purge commentaire à J+30 (temporaire, faute de mieux) | `collect/anonymize.py` |
| feat | RGPD 3bis — `collect/anonymize.py` jamais déclenché automatiquement | Service `cron` Docker (2h00 quotidien) + `make anonymize` pour exécution manuelle | `Dockerfile.cron`, `docker-compose.yml`, `Makefile` |
| feat | RGPD 4 — purge des données de facturation après prescription légale (5 ans) | `purge_old_billing_data()` dans le module CRON existant : suppression en cascade feedbacks → stagiaires → contrats → sessions → clients orphelins, cutoff `date_fin < aujourd'hui - 5 ans` | `collect/anonymize.py` |
