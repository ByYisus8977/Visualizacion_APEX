from django.http import JsonResponse
from django.shortcuts import render

from .models import METRICS, Discipline, GrowthMetric

METRIC_LABELS = {
    "teams": "Equipos / Participantes",
    "prize_pool": "Premio total (USD)",
    "duration": "Duración del evento",
}
AXIS_LABELS = [METRIC_LABELS[m] for m in METRICS]

HEATMAP_ROW_LABELS = {
    "lol-worlds": "League of Legends Worlds (2011→2025)",
    "fifa-world-cup": "FIFA World Cup (1930/1982→2026)",
    "cs2-majors": "CS2/CS:GO Majors (2013→2025)",
    "starcraft-ii": "StarCraft II GSL/WCS (2012→2023) (aprox.)",
}
RADAR_LABELS = {
    "cs2-majors": "CS2/CS:GO Majors",
    "starcraft-ii": "StarCraft II (aprox.)",
}
TREEMAP_TITLES = {
    "lol-worlds": ("League of Legends Worlds", "Títulos por región (2011–2025)"),
    "fifa-world-cup": ("FIFA World Cup", "Títulos por continente (1930–2022)"),
    "cs2-majors": ("CS2 / CS:GO Majors", "Títulos por región (2013–2025)"),
    "starcraft-ii": ("StarCraft II (WCS Global Finals)", "Títulos por país (2012–2019, aprox.)"),
}
BOXPLOT_TITLES = {
    "fifa-world-cup": ("FIFA World Cup", "Goles por partido, por década", "Goles totales por partido"),
    "lol-worlds": ("League of Legends Worlds", "Margen en eliminatorias, por era", "Diferencia de mapas"),
    "cs2-majors": ("CS2/CS:GO Majors", "Margen en series de playoffs, por era", "Margen (mapas)"),
    "starcraft-ii": ("StarCraft II WCS", "Margen en series de la llave, por era (aprox.)", "Margen (mapas)"),
}


def dashboard(request):
    disciplines = Discipline.objects.prefetch_related("growth_metrics")
    top_prize = (GrowthMetric.objects.filter(metric_name="prize_pool")
                 .select_related("discipline").order_by("-pct_change").first())

    in_contraction = []
    for d in disciplines:
        metrics = d.growth_metrics.all()
        if metrics and all(m.pct_change < 0 for m in metrics):
            in_contraction.append(d.name)

    return render(request, "dashboard.html", {
        "disciplines": disciplines,
        "top_prize": top_prize,
        "in_contraction": in_contraction,
    })


def radar_data(request):
    datasets = []
    for d in Discipline.objects.prefetch_related("radar_scores"):
        scores = {s.axis: s.normalized_value for s in d.radar_scores.all()}
        if not scores:
            continue
        datasets.append({
            "label": RADAR_LABELS.get(d.slug, d.name),
            "data": [scores.get(m, 0) for m in METRICS],
            "borderColor": d.accent_color,
            "backgroundColor": d.accent_color + "33",
            "pointBackgroundColor": d.accent_color,
            "borderDash": [6, 4] if d.is_preliminary else [],
        })
    return JsonResponse({"labels": AXIS_LABELS, "datasets": datasets})


def heatmap_data(request):
    disciplines = list(Discipline.objects.all())
    row_label = {d.id: HEATMAP_ROW_LABELS.get(d.slug, d.name) for d in disciplines}
    color = {d.id: d.accent_color for d in disciplines}

    # x e y tienen que coincidir exacto con las labels de los ejes o el plugin no dibuja la celda
    cells = [
        {
            "x": METRIC_LABELS[m.metric_name],
            "y": row_label[m.discipline_id],
            "v": m.pct_change,
            "color": color[m.discipline_id],
        }
        for m in GrowthMetric.objects.all()
    ]
    return JsonResponse({
        "data": cells,
        "x_labels": AXIS_LABELS,
        "y_labels": [row_label[d.id] for d in disciplines],
    })


def treemap_data(request):
    result = {}
    for d in Discipline.objects.prefetch_related("regional_titles"):
        titles = d.regional_titles.all()
        title, subtitle = TREEMAP_TITLES.get(d.slug, (d.name, "Títulos por región"))
        result[d.slug] = {
            "title": title,
            "subtitle": subtitle,
            "color": d.accent_color,
            "n": sum(t.title_count for t in titles),
            "tree": [
                {"region": t.region, "value": t.title_count, "pct": t.pct_of_total}
                for t in titles
            ],
        }
    return JsonResponse(result)


def boxplot_data(request):
    result = {}
    for d in Discipline.objects.prefetch_related("balance_records"):
        by_era = {}
        for record in d.balance_records.all():
            by_era.setdefault(record.era_label, []).append(record.value)
        if not by_era:
            continue

        eras = sorted(by_era)
        title, subtitle, y_label = BOXPLOT_TITLES.get(d.slug, (d.name, "", "Valor"))
        result[d.slug] = {
            "title": title,
            "subtitle": subtitle,
            "y_label": y_label,
            "color": d.accent_color,
            "labels": eras,
            # una lista de valores por era; el plugin calcula los cuartiles
            "data": [by_era[e] for e in eras],
        }
    return JsonResponse(result)
