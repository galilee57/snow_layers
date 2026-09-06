# Évolution de l'enneigement à Méribel

Projet d'étude de l'évolution de l'enneigement de la station de Méribel, avec
pour objectif de reproduire puis actualiser un graphique trouvé dans un
article à partir de données météorologiques accessibles par API.

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

Créer un environnement Python puis installer les dépendances du futur pipeline
(`pandas`, `requests` ou `httpx`, et une bibliothèque de visualisation comme
`matplotlib` ou `plotly`). Les dépendances seront figées dans un fichier
`requirements.txt` lorsque la source de données sera choisie.

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
├── README.md
├── notebooks/       # explorations et analyses reproductibles
├── reference/       # documents visuels utilisés comme référence
├── data/            # données locales, ignorées par Git sauf exemples légers
├── src/             # collecte, nettoyage et calculs réutilisables
└── outputs/         # graphiques et exports générés
```

Les répertoires `data/`, `outputs/` et `src/` seront complétés progressivement,
sans créer d'infrastructure avant d'avoir validé la source de données.
