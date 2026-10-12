from django.contrib import admin

from .models import (CompetitiveBalanceRecord, Discipline, GrowthMetric,
                     RadarScore, RegionalTitle)

admin.site.register(Discipline)
admin.site.register(GrowthMetric)
admin.site.register(RadarScore)
admin.site.register(RegionalTitle)
admin.site.register(CompetitiveBalanceRecord)
