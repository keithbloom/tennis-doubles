from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from tournament.models import Tournament, Group, TournamentGroup, Player, Team, Match
from datetime import date

class TournamentGridViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.tournament = Tournament.objects.create(
            name="Test Tournament",
            start_date=date.today(),
            status="ONGOING"
        )
        self.group = Group.objects.create(name="Group A")
        self.group2 = Group.objects.create(name="Group B")
        self.tournament_group = TournamentGroup.objects.create(
            tournament=self.tournament,
            group=self.group
        )
        TournamentGroup.objects.create(
            tournament=self.tournament,
            group=self.group2
        )
        
        # Create players
        self.players = []
        for i in range(4):
            player = Player.objects.create(
                first_name=f"Player{i+1}",
                last_name=f"Last{i+1}"
            )
            self.players.append(player)
        
        # Create teams
        self.team1 = Team.objects.create(
            player1=self.players[0],
            player2=self.players[1],
            tournament_group=self.tournament_group,
            rank=1
        )
        self.team2 = Team.objects.create(
            player1=self.players[2],
            player2=self.players[3],
            tournament_group=self.tournament_group,
            rank=2
        )

    def test_tournament_grid_renders(self):
        response = self.client.get(reverse('tournament_grid'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.group.name)

    def test_tournament_grid_shows_teams(self):
        response = self.client.get(reverse('tournament_grid'))
        self.assertContains(response, "Player1")
        self.assertContains(response, "Player2")

    def test_tournament_grid_shows_match_results(self):
        match = Match.objects.create(
            tournament=self.tournament,
            team1=self.team1,
            team2=self.team2,
            set1_team1=6, set1_team2=4,
            set2_team1=6, set2_team2=3,
            date_played=date.today()
        )
        response = self.client.get(reverse('tournament_grid'))
        self.assertContains(response, "6")
        self.assertContains(response, "4")

    def test_tournament_grid_with_withdrawn_team(self):
        self.team1.is_withdrawn = True
        self.team1.save()
        response = self.client.get(reverse('tournament_grid'))
        self.assertContains(response, 'line-through')

    def test_no_ongoing_tournament(self):
        """Test behavior when no ongoing tournament exists"""
        # Delete all ongoing tournaments
        Tournament.objects.filter(status='ONGOING').delete()

        # Create a completed tournament
        group1 = Group.objects.create(name="Completed Group 1")
        group2 = Group.objects.create(name="Completed Group 2")
        completed_tournament = Tournament.objects.create(
            name="Completed Tournament",
            start_date=date.today(),
            status="COMPLETED",
            end_date=date.today()
        )
        TournamentGroup.objects.create(tournament=completed_tournament, group=group1)
        TournamentGroup.objects.create(tournament=completed_tournament, group=group2)

        response = self.client.get(reverse('tournament_grid'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tournament/no_tournament.html')

    def test_tournament_object_in_context(self):
        """Test that tournament object is passed to context"""
        response = self.client.get(reverse('tournament_grid'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('tournament', response.context)
        self.assertEqual(response.context['tournament'], self.tournament)

    def test_tournament_name_in_header(self):
        """Test that tournament name appears in the page header"""
        response = self.client.get(reverse('tournament_grid'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.tournament.name)
        # Verify it's in the header context, not just somewhere on the page
        self.assertIn('tournament', response.context)
        self.assertEqual(response.context['tournament'].name, "Test Tournament")

class TeamsAPIViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='admin',
            password='password',
            is_staff=True
        )
        self.tournament = Tournament.objects.create(
            name="API Test Tournament",
            start_date=date.today()
        )
        self.group = Group.objects.create(name="API Group")
        self.group2 = Group.objects.create(name="API Group 2")
        self.tournament_group = TournamentGroup.objects.create(
            tournament=self.tournament,
            group=self.group
        )
        TournamentGroup.objects.create(
            tournament=self.tournament,
            group=self.group2
        )

    def test_teams_api_requires_staff(self):
        response = self.client.get(reverse('api_teams_by_tournament'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_teams_api_returns_grouped_teams(self):
        self.client.login(username='admin', password='password')

        # Create test data
        player1 = Player.objects.create(first_name="Alice", last_name="A")
        player2 = Player.objects.create(first_name="Bob", last_name="B")
        Team.objects.create(
            player1=player1,
            player2=player2,
            tournament_group=self.tournament_group
        )

        response = self.client.get(
            reverse('api_teams_by_tournament'),
            {'tournament': self.tournament.id}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], "API Group")
        self.assertEqual(len(data[0]['teams']), 1)