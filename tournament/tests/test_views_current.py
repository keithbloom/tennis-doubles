from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from tournament.models import Tournament, Group, TournamentGroup, Player, Team, Match
from tournament.views import get_standings
from datetime import date

class TournamentGridViewTest(TestCase):
    def setUp(self):
        Tournament.objects.all().delete()
        Group.objects.all().delete()
        Player.objects.all().delete()

        self.client = Client()
        self.tournament = Tournament.objects.create(
            name="Test Tournament",
            start_date=date.today(),
            status="ONGOING"
        )
        self.group = Group.objects.create(name="Group A")
        self.tournament_group = TournamentGroup.objects.create(
            tournament=self.tournament,
            group=self.group
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
        """Test that the tournament grid page renders successfully"""
        response = self.client.get(reverse('tournament_grid'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tournament/grid.html')

    def test_tournament_grid_shows_teams(self):
        """Test that teams are displayed in the grid"""
        response = self.client.get(reverse('tournament_grid'))
        self.assertContains(response, "Player1")
        self.assertContains(response, "Player2")
        self.assertContains(response, self.group.name)

    def test_tournament_grid_shows_match_results(self):
        """Test that match results are displayed correctly"""
        match = Match.objects.create(
            tournament=self.tournament,
            team1=self.team1,
            team2=self.team2,
            set1_team1=6, set1_team2=4,
            set2_team1=6, set2_team2=3,
            date_played=date.today()
        )
        response = self.client.get(reverse('tournament_grid'))
        # Check that scores appear in the response
        self.assertContains(response, "6")
        self.assertContains(response, "4")

    def test_tournament_grid_with_withdrawn_team(self):
        """Test display of withdrawn teams"""
        self.team1.is_withdrawn = True
        self.team1.save()
        response = self.client.get(reverse('tournament_grid'))
        self.assertContains(response, 'line-through')

    def test_no_ongoing_tournament(self):
        """Test behavior when no ongoing tournament exists"""
        # Clear any other tournaments
        Tournament.objects.all().delete()
        
        # Create and complete our test tournament
        self.tournament.status = "COMPLETED"
        self.tournament.end_date = date.today()
        self.tournament.save()
        
        response = self.client.get(reverse('tournament_grid'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tournament/no_tournament.html')

    def test_multiple_groups(self):
        """Test tournament with multiple groups"""
        # Create second group
        group2 = Group.objects.create(name="Group B")
        tournament_group2 = TournamentGroup.objects.create(
            tournament=self.tournament,
            group=group2
        )
        
        # Create teams for second group
        player5 = Player.objects.create(first_name="Player5", last_name="Last5")
        player6 = Player.objects.create(first_name="Player6", last_name="Last6")
        Team.objects.create(
            player1=player5,
            player2=player6,
            tournament_group=tournament_group2,
            rank=1
        )
        
        response = self.client.get(reverse('tournament_grid'))
        self.assertContains(response, "Group A")
        self.assertContains(response, "Group B")


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
        self.tournament_group = TournamentGroup.objects.create(
            tournament=self.tournament,
            group=self.group
        )

    def test_teams_api_requires_staff(self):
        """Test that API requires staff permission"""
        response = self.client.get(reverse('teams_by_tournament'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_teams_api_returns_grouped_teams(self):
        """Test API returns correctly grouped teams"""
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
            reverse('teams_by_tournament'),
            {'tournament': self.tournament.id}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], "API Group")
        self.assertEqual(len(data[0]['teams']), 1)
        self.assertEqual(data[0]['teams'][0]['name'], "Alice/Bob")


class GetStandingsTest(TestCase):
    def setUp(self):
        # Create a test tournament
        self.tournament = Tournament.objects.create(
            name="Standings Test Tournament", 
            start_date=date.today()
        )
        
        # Create a test group
        self.group = Group.objects.create(name="Standings Test Group")
        
        # Create tournament group
        self.tournament_group = TournamentGroup.objects.create(
            tournament=self.tournament,
            group=self.group
        )

        # Create test players
        self.players = []
        for i in range(4):
            player = Player.objects.create(
                first_name=f"Player{i+1}", 
                last_name=f"Last{i+1}"
            )
            self.players.append(player)

        # Create test teams
        self.team1 = Team.objects.create(
            player1=self.players[0], 
            player2=self.players[1], 
            tournament_group=self.tournament_group
        )
        self.team2 = Team.objects.create(
            player1=self.players[2], 
            player2=self.players[3], 
            tournament_group=self.tournament_group
        )

    def test_standings_with_no_matches(self):
        """Test standings when no matches have been played"""
        standings = get_standings(self.tournament.id, self.tournament_group.id)
        self.assertIsInstance(standings, list)
        self.assertEqual(len(standings), 2)
        for standing in standings:
            self.assertEqual(standing['total_points'], 0)
            self.assertEqual(standing['matches_played'], 0)

    def test_standings_with_match(self):
        """Test standings calculation with a match"""
        Match.objects.create(
            tournament=self.tournament,
            team1=self.team1,
            team2=self.team2,
            set1_team1=6, set1_team2=4,
            set2_team1=6, set2_team2=3
        )
        
        standings = get_standings(self.tournament.id, self.tournament_group.id)
        
        # Find team1's standing
        team1_standing = next(s for s in standings if s['team'] == self.team1)
        self.assertEqual(team1_standing['total_points'], 4)  # Win = 4 points
        self.assertEqual(team1_standing['matches_played'], 1)
        
        # Find team2's standing
        team2_standing = next(s for s in standings if s['team'] == self.team2)
        self.assertEqual(team2_standing['total_points'], 1)  # Loss = 1 point
        self.assertEqual(team2_standing['matches_played'], 1)

    def test_standings_sorting(self):
        """Test that standings are sorted by points"""
        # Create a third team
        player5 = Player.objects.create(first_name="Player5", last_name="Last5")
        player6 = Player.objects.create(first_name="Player6", last_name="Last6")
        team3 = Team.objects.create(
            player1=player5,
            player2=player6,
            tournament_group=self.tournament_group
        )
        
        # Team1 beats Team2
        Match.objects.create(
            tournament=self.tournament,
            team1=self.team1,
            team2=self.team2,
            set1_team1=6, set1_team2=4,
            set2_team1=6, set2_team2=3
        )
        
        # Team2 beats Team3
        Match.objects.create(
            tournament=self.tournament,
            team1=self.team2,
            team2=team3,
            set1_team1=6, set1_team2=4,
            set2_team1=6, set2_team2=3
        )
        
        standings = get_standings(self.tournament.id, self.tournament_group.id)
        
        # Check order (Team2 should be first with 5 points, then Team1 with 4, then Team3 with 1)
        self.assertEqual(standings[0]['team'], self.team2)
        self.assertEqual(standings[0]['total_points'], 5)
        self.assertEqual(standings[1]['team'], self.team1)
        self.assertEqual(standings[1]['total_points'], 4)
        self.assertEqual(standings[2]['team'], team3)
        self.assertEqual(standings[2]['total_points'], 1)