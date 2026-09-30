# Automatisation Excel Reporting

Automatisation du reporting Capitole Énergie à partir de Salesforce.

## Phase 1 — Extracteur Salesforce en lecture seule

Cette première version **n'écrit rien dans Excel**.

Elle :
- s'authentifie auprès de Salesforce via OAuth `client_credentials` ;
- exécute les requêtes du bloc **RESULTAT VENTE INTERNE** ;
- couvre l'exercice courant et/ou N-1 (1er août → 31 juillet) ;
- produit un fichier `results.json` contenant les résultats et les SOQL exécutés ;
- peut être lancée manuellement depuis GitHub Actions.

Métriques actuellement extraites :
- CA facturé ;
- CA signé ;
- CA facturé limité aux signatures du même exercice pour le taux upfront ;
- opportunités gagnées ;
- nombre de compteurs ;
- volume.

## Configuration locale

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Puis renseigner dans `.env` :

```text
SF_LOGIN_URL=https://login.salesforce.com
SF_CLIENT_ID=...
SF_CLIENT_SECRET=...
SF_API_VERSION=v66.0
```

Lancer :

```bash
python -m src.main --period both
```

Le fichier `results.json` est généré localement.

## GitHub Actions

Créer les secrets du dépôt :
- `SF_LOGIN_URL`
- `SF_CLIENT_ID`
- `SF_CLIENT_SECRET`

La variable `SF_API_VERSION` est optionnelle.

Le workflow **Salesforce readonly extract** est volontairement manuel pendant la phase de validation.

## Suite

1. Comparer les résultats Salesforce au classeur de référence.
2. Corriger toute divergence de filtre ou de logique.
3. Étendre aux autres onglets.
4. Définir une whitelist exacte des cellules Excel autorisées.
5. Ajouter seulement ensuite l'écriture Excel / SharePoint.
6. Activer la planification et les alertes.
