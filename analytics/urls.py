from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("api/heatmap/", views.heatmap_data, name="heatmap_data"),
    path("api/radar/", views.radar_data, name="radar_data"),
    path("api/treemap/", views.treemap_data, name="treemap_data"),
    path("api/boxplot/", views.boxplot_data, name="boxplot_data"),
]
