from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('verify-pending/', views.verify_pending_view, name='verify-pending'),
    path('verify-email/<uidb64>/<token>/', views.verify_email_view, name='verify-email'),
    path('forgot-password/', views.forgot_password_view, name='forgot-password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password_view, name='reset-password'),
    path('', views.home),
    path('account/', views.account_view),
    path('dashboard/', views.dashboard),
    path('nodemap/', views.node_map),
    path('alerts/', views.alerts),
    path('about/', views.about),
    path('support/', views.support),
    path("api/chart/", views.chart_data),
    path("api/nodes/", views.latest_nodes),
    path("api/nodes/<int:node_id>/history/", views.node_history),
    path("api/alerts/", views.latest_alerts),
]
