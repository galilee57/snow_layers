"""Catalogue éditorial initial, non exhaustif, de stations françaises.

Positions WGS84 et altitudes arrondies indicatives, préparées le 2026-09-10.
Ce sont des points de requête approximatifs, pas des stations météorologiques.
Référence de nomenclature : https://fr.wikipedia.org/wiki/Liste_de_stations_de_sports_d%27hiver
"""

_ROWS = [
    ('meribel', 'Méribel', 'Alpes', 45.41497, 6.565, 1450),
    ('courchevel', 'Courchevel', 'Alpes', 45.415, 6.634, 1850),
    ('val-thorens', 'Val Thorens', 'Alpes', 45.298, 6.580, 2300),
    ('les-menuires', 'Les Menuires', 'Alpes', 45.324, 6.538, 1850),
    ('tignes', 'Tignes', 'Alpes', 45.469, 6.907, 2100),
    ('val-disere', "Val d’Isère", 'Alpes', 45.448, 6.980, 1850),
    ('les-arcs', 'Les Arcs 1800', 'Alpes', 45.572, 6.779, 1800),
    ('la-plagne', 'La Plagne', 'Alpes', 45.506, 6.677, 1970),
    ('chamonix', 'Chamonix', 'Alpes', 45.924, 6.870, 1040),
    ('megeve', 'Megève', 'Alpes', 45.857, 6.617, 1110),
    ('avoriaz', 'Avoriaz', 'Alpes', 46.191, 6.775, 1800),
    ('morzine', 'Morzine', 'Alpes', 46.180, 6.709, 1000),
    ('les-gets', 'Les Gets', 'Alpes', 46.159, 6.670, 1170),
    ('la-clusaz', 'La Clusaz', 'Alpes', 45.905, 6.424, 1040),
    ('le-grand-bornand', 'Le Grand-Bornand', 'Alpes', 45.942, 6.427, 1000),
    ('les-saisies', 'Les Saisies', 'Alpes', 45.760, 6.526, 1650),
    ('alpe-dhuez', 'Alpe d’Huez', 'Alpes', 45.091, 6.069, 1860),
    ('les-deux-alpes', 'Les Deux Alpes', 'Alpes', 45.010, 6.123, 1650),
    ('serre-chevalier', 'Serre Chevalier · Chantemerle', 'Alpes', 44.934, 6.588, 1350),
    ('montgenevre', 'Montgenèvre', 'Alpes', 44.931, 6.723, 1860),
    ('vars', 'Vars · Les Claux', 'Alpes', 44.573, 6.679, 1850),
    ('risoul', 'Risoul', 'Alpes', 44.623, 6.633, 1850),
    ('isola-2000', 'Isola 2000', 'Alpes', 44.186, 7.159, 2000),
    ('auron', 'Auron', 'Alpes', 44.226, 6.931, 1600),
    ('villard-de-lans', 'Villard-de-Lans', 'Alpes', 45.070, 5.551, 1050),
    ('font-romeu', 'Font-Romeu', 'Pyrénées', 42.505, 2.040, 1800),
    ('les-angles', 'Les Angles', 'Pyrénées', 42.578, 2.074, 1650),
    ('ax-3-domaines', 'Ax 3 Domaines', 'Pyrénées', 42.701, 1.814, 1400),
    ('saint-lary', 'Saint-Lary · Pla d’Adet', 'Pyrénées', 42.815, 0.294, 1700),
    ('peyragudes', 'Peyragudes', 'Pyrénées', 42.790, 0.445, 1600),
    ('la-mongie', 'Grand Tourmalet · La Mongie', 'Pyrénées', 42.911, 0.179, 1800),
    ('cauterets', 'Cauterets · Le Lys', 'Pyrénées', 42.884, -0.135, 1850),
    ('gourette', 'Gourette', 'Pyrénées', 42.958, -0.333, 1350),
    ('la-pierre-saint-martin', 'La Pierre Saint-Martin', 'Pyrénées', 42.978, -0.745, 1650),
    ('les-rousses', 'Les Rousses', 'Jura', 46.485, 6.062, 1120),
    ('metabief', 'Métabief', 'Jura', 46.773, 6.351, 1000),
    ('monts-jura', 'Monts Jura · Lélex', 'Jura', 46.304, 5.938, 900),
    ('la-bresse', 'La Bresse · Hohneck', 'Vosges', 48.036, 6.970, 900),
    ('gerardmer', 'Gérardmer', 'Vosges', 48.053, 6.904, 900),
    ('le-lac-blanc', 'Le Lac Blanc', 'Vosges', 48.127, 7.088, 1100),
    ('super-besse', 'Super-Besse', 'Massif central', 45.509, 2.853, 1350),
    ('le-mont-dore', 'Le Mont-Dore · Le Sancy', 'Massif central', 45.542, 2.814, 1350),
    ('le-lioran', 'Le Lioran', 'Massif central', 45.083, 2.750, 1250),
    ('chalmazel', 'Chalmazel', 'Massif central', 45.697, 3.764, 1100),
    ('val-dese', 'Val d’Ese', 'Corse', 42.000, 9.125, 1600),
    ('ghisoni', 'Ghisoni · Capannelle', 'Corse', 42.077, 9.150, 1580),
]
STATIONS = [dict(zip(('slug', 'name', 'massif', 'latitude', 'longitude', 'elevation_m'), row)) for row in _ROWS]


def altitude_category(elevation_m: float) -> str:
    """Classement utilisé par la carte et les comparaisons (altitude de référence)."""
    if elevation_m < 1200:
        return "basse"
    if elevation_m <= 1800:
        return "moyenne"
    return "haute"


for station in STATIONS:
    station["altitude_category"] = altitude_category(station["elevation_m"])

STATIONS_BY_SLUG = {station['slug']: station for station in STATIONS}
CATALOG_NOTE = 'Altitudes : basse < 1 200 m, moyenne 1 200–1 800 m, haute > 1 800 m · positions approximatives'
