-- Nombre de contrats actifs par stagiaire — appelée par l'assistant
-- pour répondre à « avec qui avons-nous des contrats actifs ? ».

SELECT
    stagiaires.prenom,
    stagiaires.nom,
    COUNT(DISTINCT contrats.id) AS nb_contrats_actifs
FROM contrats
JOIN stagiaires ON contrats.session_id = stagiaires.session_id
WHERE contrats.statut = 'actif'
GROUP BY stagiaires.prenom, stagiaires.nom
ORDER BY nb_contrats_actifs DESC;
