# tournament/urls.py
from django.urls import path
from tournament import views

urlpatterns = [
    path('teams/', views.teams_by_tournament, name='teams_by_tournament'),
]