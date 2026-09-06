# Méribel Snow Layers

Projet Python/Jupyter d'analyse historique et de visualisation de
l'enneigement à Méribel à partir de données météorologiques externes.

## Tech Stack

- Python 3, Flask, Jupyter, pandas
- API HTTP et fichiers CSV ; frontend HTML, CSS et JavaScript natifs
- matplotlib ou Plotly pour les analyses hors application web

## Commands

- `jupyter lab` - ouvrir les notebooks depuis la racine du projet
- `./start_meribel_snow.command` - démarrer le prototype sur macOS
- `PYTHONPATH=src .venv/bin/python -m snow_layers.import_open_meteo --season 2024-2025` - importer une saison Open-Meteo
- `.venv/bin/python -m pip install -r requirements-dev.txt` - installer les outils de test
- `PYTHONPATH=src .venv/bin/python -m pytest` - exécuter les tests

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
- Open-Meteo Archive fournit une réanalyse de `snow_depth`, pas un relevé de
  station : conserver cette qualification dans l'API, l'interface et les exports.
- Identifier visuellement toute donnée simulée, estimée ou partielle ; ne pas
  la présenter comme une mesure observée.
- Conserver les décisions de palette, typographie et composants dans `DESIGN.md`
  et le mettre à jour avec toute modification visuelle substantielle.
- Vérifier les résultats dans une exécution réelle et utiliser `git diff --check`
  avant de considérer une modification terminée.
