# Évolution de l'enneigement à Méribel

Projet d'étude de l'évolution de l'enneigement de la station de Méribel, avec
pour objectif de reproduire puis actualiser un graphique trouvé dans un
article à partir de données météorologiques accessibles par API.

## Prototype web

Un premier prototype local est disponible. Il présente l'évolution de la
hauteur de neige par saison avec un sélecteur interactif et une API JSON.
Les valeurs initiales de Méribel sont simulées ; un import explicite permet de
charger la réanalyse Open-Meteo pour la station choisie.

Sur macOS, double-cliquer sur `start_meribel_snow.command`, ou lancer :

```bash
./start_meribel_snow.command
```

Le lanceur crée `.venv`, installe les dépendances puis ouvre
`http://127.0.0.1:5000`. Garder la fenêtre Terminal ouverte pendant
l'utilisation ; `Ctrl+C` arrête le serveur.

L'API du prototype est accessible à `GET /api/snow-depth`. Son contrat est
prêt à recevoir une source réelle sans modifier l'interface.

Les choix graphiques sont détaillés dans [DESIGN.md](DESIGN.md).

### Importer une saison réelle

Le projet utilise désormais [Open-Meteo Archive](https://open-meteo.com/en/docs/historical-weather-api),
une API ouverte sans clé. Elle fournit une **réanalyse modélisée** de la hauteur
de neige au sol ; ce n'est pas une mesure relevée à la station. Les valeurs
horaires sont converties de mètres en centimètres puis moyennées par journée.

Importer une saison complète dans la base SQLite locale :

```bash
PYTHONPATH=src .venv/bin/python -m snow_layers.import_open_meteo --season 2024-2025
```

La base est créée dans `data/snow_layers.sqlite` et reste ignorée par Git. Vous
pouvez importer plusieurs saisons ; la même commande met à jour les jours déjà
présents. Redémarrer ensuite l'application. Dès qu'une saison est présente, le
prototype remplace ses données simulées par les observations importées.

La base comprend `stations` (position et altitude de référence) et
`snow_observations` (date, hauteur en cm, source, URL de la requête et date
d'import). Une contrainte d'unicité empêche les doublons pour une même station,
date et source.

## État du projet

Le dépôt contient actuellement les premiers essais exploratoires :

- `notebooks/01_stormglass_exploration.ipynb` : appel historique à
  l'API Stormglass et premiers graphiques ;
- `notebooks/02_openweather_import_exploration.ipynb` : exploration d'un CSV
  exporté depuis OpenWeather/Google Drive ;
- `reference/meribel_snow_graph.jpg` : image du graphique à reproduire.

Ces notebooks ne constituent pas encore un pipeline reproductible. L'API
Stormglass utilisée dans l'essai est soumise à des limites ou à une offre
payante, et la clé présente dans l'ancien notebook ne doit pas être réutilisée.

## Objectifs

1. Identifier une source de données exploitable dans la durée (API gratuite,
   données ouvertes ou téléchargement officiel).
2. Collecter les observations de façon reproductible, avec cache local et
   limitation du nombre de requêtes.
3. Harmoniser les dates, unités, altitude et définition de la hauteur de neige.
4. Comparer les saisons de ski et reproduire le graphique de référence.
5. Mettre à jour la visualisation avec des données nouvelles en conservant la
   traçabilité de la source et de la date de collecte.

## Démarrage

Créer un environnement Python puis installer les dépendances :

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Pour exécuter les tests, installer aussi les dépendances de développement :

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
PYTHONPATH=src .venv/bin/python -m pytest
```

Lancer ensuite Jupyter depuis la racine :

```bash
jupyter lab
```

Les notebooks actuels peuvent servir de support de lecture, mais leurs chemins
de fichiers et leurs appels réseau devront être adaptés avant toute
réutilisation.

## Données et sécurité

- Ne jamais enregistrer de clé API dans un notebook, un CSV ou Git ; utiliser
  une variable d'environnement ou un fichier `.env` ignoré.
- Conserver les données brutes séparément des données nettoyées et noter leur
  source, période, unité et date de téléchargement.
- Ne pas multiplier les requêtes : privilégier le cache local, les fenêtres de
  collecte raisonnables et les données ouvertes quand elles existent.
- Vérifier la licence et les conditions d'utilisation avant publication.

## Structure

```text
.
├── AGENTS.md
├── DESIGN.md       # décisions visuelles du prototype
├── README.md
├── app.py          # point d'entrée de l'application Flask
├── notebooks/       # explorations et analyses reproductibles
├── reference/       # documents visuels utilisés comme référence
├── data/            # données locales, ignorées par Git sauf exemples légers
├── src/             # collecte, nettoyage, API et calculs réutilisables
├── static/          # styles et interactions du frontend
├── templates/       # pages HTML rendues par Flask
└── outputs/         # graphiques et exports générés
```

Les répertoires `data/`, `outputs/` et `src/` seront complétés progressivement,
sans créer d'infrastructure avant d'avoir validé la source de données.

## Carte des stations françaises

La carte permet de sélectionner l'une des 46 stations du catalogue initial
(Alpes, Pyrénées, Jura, Vosges, Massif central, Corse). Une liste alphabétique
synchronisée reste utilisable si la carte ne charge pas. Cliquez sur une station,
choisissez une saison terminée, puis **Charger l’enneigement**. Chaque station a
ses propres données SQLite ; les saisons complètes sont réutilisées sans nouvel
appel météo. La démonstration demeure réservée à Méribel.

Le catalogue éditorial `src/snow_layers/stations.py` est **non exhaustif** : noms
référencés par la [liste des stations de sports d’hiver](https://fr.wikipedia.org/wiki/Liste_de_stations_de_sports_d%27hiver),
positions WGS84 en degrés et altitudes en mètres **approximatives**, préparées le
10 septembre 2026. Il ne s'agit pas d'un inventaire officiel ou de positions de
capteurs. Le point représente une localité ou un départ de domaine, pas son sommet.
La requête météo utilise ce point et cette altitude explicitement.

La période demandée est du 1er décembre au 30 avril ; valeurs en cm, moyennes
quotidiennes des hauteurs horaires de la réanalyse ERA5-Land Open-Meteo (pas un
relevé de station). Source, altitude, période et date de collecte sont affichées.
Les imports incomplets sont signalés et peuvent être redemandés.

La carte utilise [Leaflet 1.9.4](https://leafletjs.com/examples/quick-start/) via
unpkg et les tuiles OpenStreetMap, avec attribution. Leur affichage requiert Internet.
Le catalogue et les séries déjà importées restent locaux. Aucun service payant
ni clé n'est ajouté ; les limites du service public Open-Meteo s'appliquent.

API : `GET /api/stations`, `GET /api/snow-depth?station=tignes` et
`POST /api/snow-depth/import` avec `{"station":"tignes","season":"2024-2025"}`.
Import en ligne de commande :

```bash
PYTHONPATH=src .venv/bin/python -m snow_layers.import_open_meteo --station tignes --season 2024-2025
```

Pour constituer la base comparative complète, la commande historique découpe
la période en tranches de dix ans et regroupe quatre stations par requête :

```bash
PYTHONPATH=src .venv/bin/python -m snow_layers.import_all_history --from-year 1950 --to-year 2025
```

Elle couvre les saisons 1950-1951 à 2025-2026, conserve les réponses brutes
dans `data/raw/open_meteo_archive/` et reprend automatiquement les tranches
déjà téléchargées. La limite publique Open-Meteo peut imposer une attente ou
un redémarrage ultérieur ; les stations et tranches validées restent acquises.
