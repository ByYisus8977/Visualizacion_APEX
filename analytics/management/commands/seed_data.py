import csv

from django.conf import settings
from django.core.management.base import BaseCommand

from analytics.models import (METRICS, CompetitiveBalanceRecord, Discipline,
                              GrowthMetric, RadarScore, RegionalTitle)

DATASETS = settings.BASE_DIR / "Datasets"

# slug, nombre, color, riesgo, preliminar
DISCIPLINES = [
    ("lol-worlds", "LoL Worlds", "#D93025", "high", False),
    ("fifa-world-cup", "FIFA World Cup", "#FFD52E", "low", False),
    ("cs2-majors", "CS2 Majors", "#E8871E", "medium", False),
    ("starcraft-ii", "StarCraft II", "#4E9ACB", "low", True),
]

# % de cambio en (equipos, premio, duración)
GROWTH = {
    "lol-worlds": (112, 4976, 1200),
    "fifa-world-cup": (269, 3175, 124),
    "cs2-majors": (100, 400, 567),  # 16 -> 32 equipos, US$250K -> 1.25M, 3 -> 20 días
    "starcraft-ii": (-56.3, -82.7, -36.4),
}

# Tasa final/inicial de cada eje, escalada a 100 = la más alta entre las cuatro
RADAR = {
    "lol-worlds": (57.6, 100, 100),
    "fifa-world-cup": (100, 64.5, 17.2),
    "cs2-majors": (54.2, 9.8, 51.3),
    "starcraft-ii": (6.1, 2.4, 8.9),
}

# (región, títulos, % del total)
TITLES = {
    "lol-worlds": [("Corea", 10, 67), ("China", 3, 20), ("Europa", 1, 7), ("Taiwan/HK/Macau", 1, 7)],
    "fifa-world-cup": [("Europa", 12, 55), ("Sudamérica", 10, 45)],
    "cs2-majors": [("Europa", 13, 59), ("CIS", 6, 27), ("Brasil", 2, 9), ("N. América", 1, 5)],
    "starcraft-ii": [("Corea del Sur", 7, 88), ("Otros (Finlandia)", 1, 12)],
}

# (etiqueta, último año que incluye)
ERAS = {
    "lol-worlds": [("2011-15", 2015), ("2016-20", 2020), ("2021-25", 2025)],
    "cs2-majors": [("2013-16", 2016), ("2017-19", 2019), ("2020-26", 2026)],
    "starcraft-ii": [("2012-14", 2014), ("2015-17", 2017), ("2018-19", 2019)],
}


def era_for(slug, year):
    for label, last_year in ERAS[slug]:
        if year <= last_year:
            return label
    raise ValueError(f"{year} no cae en ninguna era de {slug}")


def read_csv(*path):
    with open(DATASETS.joinpath(*path), encoding="utf-8") as f:
        return list(csv.DictReader(f))


class Command(BaseCommand):
    help = "Borra y vuelve a cargar todos los datos de APEX."

    def handle(self, *args, **options):
        Discipline.objects.all().delete()  # el resto se borra en cascada

        disciplines = {
            slug: Discipline.objects.create(
                slug=slug, name=name, accent_color=color, risk_level=risk, is_preliminary=prelim)
            for slug, name, color, risk, prelim in DISCIPLINES
        }

        for slug, values in GROWTH.items():
            for metric, value in zip(METRICS, values):
                GrowthMetric.objects.create(
                    discipline=disciplines[slug], metric_name=metric, pct_change=value)

        for slug, values in RADAR.items():
            for metric, value in zip(METRICS, values):
                RadarScore.objects.create(
                    discipline=disciplines[slug], axis=metric, normalized_value=value)

        for slug, rows in TITLES.items():
            for region, count, pct in rows:
                RegionalTitle.objects.create(
                    discipline=disciplines[slug], region=region, title_count=count, pct_of_total=pct)

        CompetitiveBalanceRecord.objects.bulk_create(
            CompetitiveBalanceRecord(discipline=disciplines[slug], era_label=era, value=value)
            for slug, era, value in self.balance_rows()
        )
        self.stdout.write(self.style.SUCCESS("Datos cargados."))

    def balance_rows(self):
        # FIFA: goles totales por partido, agrupados por década
        for r in read_csv("fifa_dataset", "wc_all_matches.csv"):
            decade = int(r["year"]) // 10 * 10
            yield "fifa-world-cup", f"{decade}s", int(r["score1"]) + int(r["score2"])

        # LoL: diferencia de mapas en eliminatorias ("3-1" -> 2)
        for r in read_csv("lol_dataset", "03_Worlds_Knockout_Bracket_Results.csv"):
            a, b = r["Score"].split("-")
            yield "lol-worlds", era_for("lol-worlds", int(r["Year"])), abs(int(a) - int(b))

        for r in read_csv("cs2_dataset", "cs_majors_playoff_series.csv"):
            yield "cs2-majors", era_for("cs2-majors", int(r["year"])), int(r["margin"])

        for r in read_csv("sc2_dataset", "sc2_wcs_global_finals_bracket.csv"):
            yield "starcraft-ii", era_for("starcraft-ii", int(r["year"])), int(r["margin"])
