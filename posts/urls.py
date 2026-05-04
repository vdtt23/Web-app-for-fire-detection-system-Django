from django.urls import path
from . import views

urlpatterns = [
    path('', views.home),
    path('dashboard/', views.dashboard),
    path('nodemap/', views.node_map),
    path('alerts/', views.alerts),
    path('about/', views.about),
    path('support/', views.support),
    path("api/chart/", views.chart_data),
    path("api/nodes/", views.latest_nodes),
    path("api/alerts/", views.latest_alerts),
]