from django.db import models

METRIC_CHOICES = [
    ("teams", "Equipos"),
    ("prize_pool", "Premio total"),
    ("duration", "Duración"),
]
METRICS = [key for key, _ in METRIC_CHOICES]


class Discipline(models.Model):
    RISK_CHOICES = [("low", "Bajo"), ("medium", "Medio"), ("high", "Alto")]

    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    accent_color = models.CharField(max_length=7)
    risk_level = models.CharField(max_length=6, choices=RISK_CHOICES)
    is_preliminary = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class GrowthMetric(models.Model):
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, related_name="growth_metrics")
    metric_name = models.CharField(max_length=12, choices=METRIC_CHOICES)
    pct_change = models.FloatField()

    def __str__(self):
        return f"{self.discipline} - {self.metric_name}: {self.pct_change}%"


class RadarScore(models.Model):
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, related_name="radar_scores")
    axis = models.CharField(max_length=12, choices=METRIC_CHOICES)
    normalized_value = models.FloatField()

    def __str__(self):
        return f"{self.discipline} - {self.axis}: {self.normalized_value}"


class RegionalTitle(models.Model):
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, related_name="regional_titles")
    region = models.CharField(max_length=50)
    title_count = models.PositiveIntegerField()
    pct_of_total = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.discipline} - {self.region}: {self.title_count}"


class CompetitiveBalanceRecord(models.Model):
    # Un registro por partido o serie: el boxplot necesita los valores crudos, no promedios.
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, related_name="balance_records")
    era_label = models.CharField(max_length=20)
    value = models.FloatField()

    def __str__(self):
        return f"{self.discipline} {self.era_label}: {self.value}"
