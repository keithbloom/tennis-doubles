# tournament/tests/test_tournament_history_view.py
from django.test import TestCase
from django.urls import reverse
from datetime import date
from tournament.models import Tournament, Group, TournamentGroup


class TournamentHistoryViewTest(TestCase):
    def setUp(self):
        """Create multiple test tournaments"""
        self.tournaments = []
        for i in range(1, 5):
            is_completed = i < 3
            tournament = Tournament.objects.create(
                name=f'Tournament {i}',
                start_date=date(2026, i, 1),
                status='COMPLETED' if is_completed else 'ONGOING',
                end_date=date(2026, i, 15) if is_completed else None
            )
            self.tournaments.append(tournament)

        # Add groups to tournaments (need at least 2 groups per tournament)
        group1 = Group.objects.create(name='Test Group 1')
        group2 = Group.objects.create(name='Test Group 2')
        for tournament in self.tournaments:
            TournamentGroup.objects.create(tournament=tournament, group=group1)
            TournamentGroup.objects.create(tournament=tournament, group=group2)

    def test_tournament_history_view_lists_all_tournaments(self):
        """View should list all tournaments in reverse chronological order"""
        response = self.client.get(reverse('tournament_history'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('tournaments', response.context)

        tournaments = list(response.context['tournaments'])

        # Filter to only test tournaments (exclude migration-created ones)
        test_tournaments = [t for t in tournaments if t.name.startswith('Tournament ')]
        self.assertEqual(len(test_tournaments), 4)

        # Verify reverse chronological order (newest first)
        self.assertEqual(test_tournaments[0].name, 'Tournament 4')
        self.assertEqual(test_tournaments[3].name, 'Tournament 1')

    def test_tournament_history_view_shows_tournament_details(self):
        """View should display tournament names, dates, and status"""
        response = self.client.get(reverse('tournament_history'))

        for tournament in self.tournaments:
            self.assertContains(response, tournament.name)
