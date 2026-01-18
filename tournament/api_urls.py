# tournament/api_urls.py
from django.urls import path
from tournament import views

urlpatterns = [
    path('teams/', views.teams_by_tournament, name='api_teams_by_tournament'),
    path('previous-partner/', views.previous_partner, name='api_previous_partner'),
]
