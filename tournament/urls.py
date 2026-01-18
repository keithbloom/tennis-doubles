# tournament/urls.py
from django.urls import path
from tournament import views

urlpatterns = [
    path('tournament/<int:tournament_id>/', views.TournamentDetailView.as_view(), name='tournament_detail'),
    path('tournaments/', views.TournamentHistoryView.as_view(), name='tournament_history'),
]