from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from ..models import Player, Group, Team, Match, Tournament, TournamentGroup
from datetime import date, timedelta

class PlayerModelTest(TestCase):
    def test_player_creation(self):
        player = Player.objects.create(first_name="John", last_name="Doe")
        self.assertEqual(str(player), "John Doe")

class TournamentModelTest(TestCase):
    def test_tournament_creation(self):
        tournament = Tournament.objects.create(
            name="Test Tournament", 
            start_date=date.today(),
            status="ONGOING"
        )
        self.assertEqual(str(tournament), "Test Tournament")
    
    def test_tournament_validation(self):
        start_date = date.today()
        end_date = start_date - timedelta(days=1)
        
        with self.assertRaises(ValidationError):
            Tournament.objects.create(
                name="Invalid Tournament",
                start_date=start_date,
                end_date=end_date  # End date before start date
            )
        
        with self.assertRaises(ValidationError):
            Tournament.objects.create(
                name="Invalid Completed Tournament",
                start_date=start_date,
                status="COMPLETED"  # Completed without end date
            )

class GroupModelTest(TestCase):
    def test_group_creation(self):
        group = Group.objects.create(name="Group A")
        self.assertEqual(str(group), "Group A")

class TournamentGroupModelTest(TestCase):
    def setUp(self):
        self.tournament = Tournament.objects.create(
            name="Test Tournament", 
            start_date=date.today()
        )
        self.group = Group.objects.create(name="Group A")
    
    def test_tournament_group_creation(self):
        tournament_group = TournamentGroup.objects.create(
            tournament=self.tournament,
            group=self.group
        )
        self.assertEqual(str(tournament_group), "Group A in Test Tournament")
    
    def test_tournament_group_unique_constraint(self):
        TournamentGroup.objects.create(
            tournament=self.tournament,
            group=self.group
        )
        with self.assertRaises(IntegrityError):
            TournamentGroup.objects.create(
                tournament=self.tournament,
                group=self.group
            )

class TeamModelTest(TestCase):
    def setUp(self):
        self.tournament = Tournament.objects.create(
            name="Test Tournament", 
            start_date=date.today()
        )
        self.group = Group.objects.create(name="Group A")
        self.tournament_group = TournamentGroup.objects.create(
            tournament=self.tournament,
            group=self.group
        )
        self.player1 = Player.objects.create(first_name="John", last_name="Doe")
        self.player2 = Player.objects.create(first_name="Jane", last_name="Smith")

    def test_team_creation(self):
        team = Team.objects.create(
            player1=self.player1, 
            player2=self.player2, 
            tournament_group=self.tournament_group
        )
        self.assertEqual(str(team), "John/Jane")

    def test_team_same_player_validation(self):
        with self.assertRaises(ValidationError):
            Team.objects.create(
                player1=self.player1, 
                player2=self.player1, 
                tournament_group=self.tournament_group
            )

    def test_team_unique_constraint(self):
        Team.objects.create(
            player1=self.player1, 
            player2=self.player2, 
            tournament_group=self.tournament_group
        )
        with self.assertRaises(IntegrityError):
            Team.objects.create(
                player1=self.player1, 
                player2=self.player2, 
                tournament_group=self.tournament_group
            )

class MatchModelTest(TestCase):
    def setUp(self):
        self.tournament = Tournament.objects.create(
            name="Test Tournament", 
            start_date=date.today()
        )
        self.group = Group.objects.create(name="Group A")
        self.tournament_group = TournamentGroup.objects.create(
            tournament=self.tournament,
            group=self.group
        )
        self.player1 = Player.objects.create(first_name="John", last_name="Doe")
        self.player2 = Player.objects.create(first_name="Jane", last_name="Smith")
        self.player3 = Player.objects.create(first_name="Bob", last_name="Johnson")
        self.player4 = Player.objects.create(first_name="Alice", last_name="Brown")
        
        self.team1 = Team.objects.create(
            player1=self.player1, 
            player2=self.player2, 
            tournament_group=self.tournament_group
        )
        self.team2 = Team.objects.create(
            player1=self.player3, 
            player2=self.player4, 
            tournament_group=self.tournament_group
        )

    def test_match_creation(self):
        match = Match.objects.create(
            tournament=self.tournament,
            team1=self.team1,
            team2=self.team2,
            set1_team1=6,
            set1_team2=4,
            set2_team1=6,
            set2_team2=3,
            date_played=date.today()
        )
        self.assertEqual(str(match), f"{self.team1} vs {self.team2} ({self.tournament})")

    def test_match_score_calculation(self):
        match = Match.objects.create(
            tournament=self.tournament,
            team1=self.team1,
            team2=self.team2,
            set1_team1=6,
            set1_team2=4,
            set2_team1=6,
            set2_team2=3
        )
        self.assertEqual(match.get_score(), "4-1")

    def test_match_validation_different_groups(self):
        group_b = Group.objects.create(name="Group B")
        tournament_group_b = TournamentGroup.objects.create(
            tournament=self.tournament,
            group=group_b
        )
        team3 = Team.objects.create(
            player1=self.player3, 
            player2=self.player4, 
            tournament_group=tournament_group_b
        )
        with self.assertRaises(ValidationError):
            Match.objects.create(
                tournament=self.tournament,
                team1=self.team1,
                team2=team3,
                set1_team1=6,
                set1_team2=4,
                set2_team1=6,
                set2_team2=3
            )

    def test_match_validation_different_tournaments(self):
        tournament2 = Tournament.objects.create(
            name="Test Tournament 2", 
            start_date=date.today()
        )
        tournament_group2 = TournamentGroup.objects.create(
            tournament=tournament2,
            group=self.group
        )
        team3 = Team.objects.create(
            player1=self.player3, 
            player2=self.player4, 
            tournament_group=tournament_group2
        )
        with self.assertRaises(ValidationError):
            Match.objects.create(
                tournament=self.tournament,
                team1=self.team1,
                team2=team3,
                set1_team1=6,
                set1_team2=4,
                set2_team1=6,
                set2_team2=3
            )

    def test_match_validation_no_clear_winner(self):
        with self.assertRaises(ValidationError):
            Match.objects.create(
                tournament=self.tournament,
                team1=self.team1,
                team2=self.team2,
                set1_team1=6,
                set1_team2=4,
                set2_team1=4,
                set2_team2=6
            )

    def test_match_with_third_set(self):
        match = Match.objects.create(
            tournament=self.tournament,
            team1=self.team1,
            team2=self.team2,
            set1_team1=6,
            set1_team2=4,
            set2_team1=4,
            set2_team2=6,
            set3_team1=7,
            set3_team2=5
        )
        self.assertEqual(match.get_score(), "4-2")