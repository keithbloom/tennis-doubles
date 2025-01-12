from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from ..models import Player, Group, Team, Match
from datetime import date
from unittest import skip

class PlayerModelTest(TestCase):
    def test_player_creation(self):
        player = Player.objects.create(first_name="John", last_name="Doe")
        self.assertEqual(str(player), "John Doe")

@skip("Skip until updated")
class GroupModelTest(TestCase):
    def test_group_creation(self):
        group = Group.objects.create(name="Group A")
        self.assertEqual(str(group), "Group A")

@skip("Skip until updated")
class TeamModelTest(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="Group A")
        self.player1 = Player.objects.create(first_name="John", last_name="Doe")
        self.player2 = Player.objects.create(first_name="Jane", last_name="Smith")

    def test_team_creation(self):
        team = Team.objects.create(player1=self.player1, player2=self.player2, group=self.group)
        self.assertEqual(str(team), "John/Jane")

    def test_team_same_player_validation(self):
        with self.assertRaises(ValidationError):
            Team.objects.create(player1=self.player1, player2=self.player1, group=self.group)

    def test_team_unique_constraint(self):
        Team.objects.create(player1=self.player1, player2=self.player2, group=self.group)
        with self.assertRaises(IntegrityError):
            Team.objects.create(player1=self.player1, player2=self.player2, group=self.group)

@skip("Skip until updated")
class MatchModelTest(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="Group A")
        self.player1 = Player.objects.create(first_name="John", last_name="Doe")
        self.player2 = Player.objects.create(first_name="Jane", last_name="Smith")
        self.player3 = Player.objects.create(first_name="Bob", last_name="Johnson")
        self.player4 = Player.objects.create(first_name="Alice", last_name="Brown")
        self.team1 = Team.objects.create(player1=self.player1, player2=self.player2, group=self.group)
        self.team2 = Team.objects.create(player1=self.player3, player2=self.player4, group=self.group)

    def test_match_creation(self):
        match = Match.objects.create(
            team1=self.team1,
            team2=self.team2,
            set1_team1=6,
            set1_team2=4,
            set2_team1=6,
            set2_team2=3,
            date_played=date.today()
        )
        self.assertEqual(str(match), f"{self.team1} vs {self.team2}")

    def test_match_score_calculation(self):
        match = Match.objects.create(
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
        team3 = Team.objects.create(player1=self.player3, player2=self.player4, group=group_b)
        with self.assertRaises(ValidationError):
            Match.objects.create(
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
                team1=self.team1,
                team2=self.team2,
                set1_team1=6,
                set1_team2=4,
                set2_team1=4,
                set2_team2=6
            )

    def test_match_with_third_set(self):
        match = Match.objects.create(
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
