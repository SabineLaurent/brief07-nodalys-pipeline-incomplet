 SELECT
    (SELECT COUNT(*) FROM clients)    AS clients,
    (SELECT COUNT(*) FROM contrats)   AS contrats,
    (SELECT COUNT(*) FROM feedbacks)  AS feedbacks,
    (SELECT COUNT(*) FROM sessions)   AS sessions,
    (SELECT COUNT(*) FROM stagiaires) AS stagiaires;
    