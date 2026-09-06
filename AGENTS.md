# Méribel Snow Layers

Projet Python/Jupyter d'analyse historique et de visualisation de
l'enneigement à Méribel à partir de données météorologiques externes.

## Tech Stack

- Python, Jupyter, pandas
- API HTTP et fichiers CSV
- matplotlib ou Plotly pour les visualisations

## Commands

- `jupyter lab` - ouvrir les notebooks depuis la racine du projet
- `.venv/bin/python -m pytest` - exécuter les tests lorsqu'ils seront ajoutés

## Rules

Les règles détaillées se trouvent dans `.agents/rules/` :

(Aucune règle modulaire pour le moment.)

## Universal Rules

- **CRITICAL** : ne jamais committer de clé API, token, cookie ou donnée
  personnelle ; utiliser des variables d'environnement et un exemple anonymisé.
- Toujours documenter la source, les unités, la période, l'altitude et la date
  de collecte des données utilisées dans une analyse.
- Préserver les notebooks d'exploration comme historique ; placer les nouveaux
  traitements réutilisables dans `src/` et les sorties générées dans `outputs/`.
- Limiter les appels API et privilégier un cache local ; ne pas dépendre d'un
  service payant sans le signaler clairement dans la documentation.
- Vérifier les résultats dans une exécution réelle et utiliser `git diff --check`
  avant de considérer une modification terminée.
