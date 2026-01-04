# tournament/tests/test_tournament_detail_view.py
from django.test import TestCase
from django.urls import reverse
from datetime import date
from tournament.models import Tournament, Group, TournamentGroup


class TournamentDetailViewTest(TestCase):
    def setUp(self):
        """Create test tournaments"""
        self.tournament1 = Tournament.objects.create(
            name='Tournament 1',
            start_date=date(2026, 1, 1),
            status='COMPLETED',
            end_date=date(2026, 1, 15)
        )
        self.tournament2 = Tournament.objects.create(
            name='Tournament 2',
            start_date=date(2026, 2, 1),
            status='ONGOING'
        )

        # Create groups for tournaments
        group1 = Group.objects.create(name='Group A')
        group2 = Group.objects.create(name='Group B')

        TournamentGroup.objects.create(tournament=self.tournament1, group=group1)
        TournamentGroup.objects.create(tournament=self.tournament1, group=group2)
        TournamentGroup.objects.create(tournament=self.tournament2, group=group1)
        TournamentGroup.objects.create(tournament=self.tournament2, group=group2)

    def test_tournament_detail_view_shows_specific_tournament(self):
        """View should display the requested tournament"""
        response = self.client.get(
            reverse('tournament_detail', args=[self.tournament1.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tournament 1')
        self.assertIn('tournament', response.context)
        self.assertEqual(response.context['tournament'], self.tournament1)

    def test_tournament_detail_view_404_for_invalid_id(self):
        """View should return 404 for non-existent tournament"""
        response = self.client.get(
            reverse('tournament_detail', args=[9999])
        )

        self.assertEqual(response.status_code, 404)
