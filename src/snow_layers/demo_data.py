"""Données temporaires utilisées par le prototype visuel.

Elles ne représentent pas des mesures réelles et seront remplacées par une
source documentée dans ``data/processed``.
"""

from __future__ import annotations

from datetime import date, timedelta


def _season(start_year: int, peak_depth_cm: int, offset: int = 0) -> list[dict[str, str | int]]:
    """Retourne une courbe de démonstration bihebdomadaire pour une saison."""
    start = date(start_year, 12, 1)
    proportions = (0.08, 0.17, 0.31, 0.48, 0.68, 0.82, 1.0, 0.91, 0.74, 0.53, 0.31, 0.16)
    return [
        {
            "date": (start + timedelta(days=index * 14)).isoformat(),
            "depth_cm": round(peak_depth_cm * proportion) + offset,
        }
        for index, proportion in enumerate(proportions)
    ]


DEMO_SEASONS = {
    "2023-2024": _season(2023, 214, -4),
    "2024-2025": _season(2024, 167, 3),
    "2025-2026": _season(2025, 192),
}
