-- Nombre de stagiaires inscrits par session, avec le client commanditaire.
-- Résultat trié du plus grand au plus petit effectif.
-- Les sessions sans stagiaires apparaissent avec nb_stagiaires = 0 (LEFT JOIN).

SELECT
    sessions.titre,                          -- intitulé de la session
    clients.raison_sociale AS client,        -- entreprise qui a commandé la formation
    COUNT(stagiaires.id) AS nb_stagiaires    -- 0 si aucun inscrit
FROM sessions
JOIN clients ON clients.id = sessions.client_id          -- chaque session appartient à un client
LEFT JOIN stagiaires ON stagiaires.session_id = sessions.id  -- LEFT : garde les sessions vides
GROUP BY sessions.id, sessions.titre, client  -- une ligne par session
ORDER BY nb_stagiaires DESC;                  -- les plus remplies en premier
