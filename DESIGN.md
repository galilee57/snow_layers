# Design · Méribel neige

Ce document fige les choix visuels du prototype afin que les évolutions
restent cohérentes avec l'interface initiale.

## Intention

Une interface éditoriale, sobre et alpine : beaucoup d'espace, des données
lisibles, et un rouge franc utilisé uniquement pour guider le regard. Le
graphique est le point focal ; la couleur ne doit jamais suggérer un niveau de
risque ou une information scientifique à elle seule.

## Palette

La couleur directrice demandée est le rouge `#DD2222`, sélectionné via le
[configurateur Tailwind de Coolors](https://coolors.co/tailwind/dd2222).

| Rôle | Couleur | Usage |
| --- | --- | --- |
| Accent | `#DD2222` | courbe, repères, titres éditoriaux, logo |
| Accent sombre | `#AD1717` | interactions futures et états actifs |
| Encre | `#191919` | texte principal et carte d'analyse |
| Neige | `#F7F7F4` | fond de page doux |
| Papier | `#FFFFFF` | surfaces de données |
| Ligne | `#DFDFDB` | séparateurs et grille secondaire |
| Texte secondaire | `#696969` | contexte, sources et descriptions |

## Typographie et composition

- Tailwind CSS v4 est la source de vérité des styles d'interface, avec les
  tokens déclarés dans `static/input.css` et le CSS compilé dans
  `static/styles.css`.
- Police système sans sérif pour l'interface, afin de garder le prototype
  rapide et sans dépendance externe.
- Georgia uniquement pour l'accent éditorial dans le titre principal.
- Titre très ample, aligné à gauche ; corps de texte limité en largeur.
- Cartes à coins arrondis de 18 px, bordures fines et ombres absentes.
- Une colonne principale pour la courbe, une colonne latérale pour sa lecture.

Le build frontend se fait avec `npm run build:css` et le mode développement
avec `npm run watch:css`. Les styles propres au SVG et à l'infobulle restent
dans la couche `@layer components` de `static/input.css`, tandis que la mise
en page est exprimée par les classes utilitaires directement dans le template.

## Données et états

- Le badge « Prototype · données simulées » est permanent tant que la source
  réelle n'est pas branchée.
- La source et le statut de la donnée apparaissent sous le graphique.
- Les mesures restent exprimées en centimètres ; toute autre unité doit être
  convertie et indiquée explicitement.
- Le changement de saison garde le graphique et le résumé synchronisés.
- Le survol ou le focus clavier d'un point affiche sa date et sa hauteur dans
  une infobulle sombre, sans masquer la courbe.
- L'axe des abscisses conserve tous les points de la série, mais n'affiche que
  quelques dates régulièrement espacées (avec le début et la fin de saison),
  pour éviter la superposition des libellés.
- La saison sélectionnée est tracée en rouge au-dessus d'une bande historique
  min–max et d'une moyenne calculées sur les autres saisons disponibles.

## Accessibilité

- Le rouge est un accent et jamais l'unique moyen d'interpréter une donnée.
- Les éléments interactifs sont de vrais contrôles HTML accessibles au clavier.
- Les points du graphique portent une valeur textuelle au survol et pour les
  technologies d'assistance.
- La mise en page passe en une colonne sur mobile.

## Sélection géographique

- Une carte Leaflet/OpenStreetMap de France précède le graphique, hauteur 420 px
  (350 px sur mobile), dans une carte blanche aux coins de 18 px.
- Repères gris, repère sélectionné rouge avec double contour et nom textuel.
- La liste alphabétique synchronisée offre une alternative clavier ou sans carte.
- Le nom, le massif et les coordonnées/altitude approximatives du point de requête
  restent visibles, ainsi que le caractère non exhaustif du catalogue.
- Un bouton explicite charge décembre–avril pour la station et la saison choisies.
  Le changement de station efface immédiatement l'ancienne courbe ; une réponse
  tardive ne peut pas réafficher les données d'une autre station.
- États distincts : chargement, aucune donnée, erreur, simulation Méribel,
  réanalyse locale et import partiel. La sélection est conservée dans l'URL.
