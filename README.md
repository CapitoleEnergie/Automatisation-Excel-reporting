# Automatisation Excel Reporting

Automatisation du reporting Capitole Énergie à partir de Salesforce, avec une première phase strictement en lecture seule.

## Phase 1

- Authentification Salesforce via OAuth client credentials
- Exécution des requêtes SOQL du reporting
- Normalisation des résultats
- Génération d'un fichier `results.json`
- Comparaison avec les chiffres du classeur avant toute écriture

> Aucun secret ne doit être commité dans ce dépôt. Les identifiants Salesforce seront stockés dans des variables d'environnement locales puis dans GitHub Actions Secrets.
