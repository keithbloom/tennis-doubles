from django.test import TestCase
from tournament.services import (
    MatchResultService, StandingsCalculator, TournamentGridBuilder
)
from tournament.models import Tournament, Group, TournamentGroup, Player, Team, Match
from datetime import date

class MatchResultServiceTest(TestCase):
    def setUp(self):
        self.tournament = Tournament.objects.create(
            name="Service Test",
            start_date=date.today()
        )
        self.group = Group.objects.create(name="Test Group")
        self.tournament_group = TournamentGroup.objects.create(
            tournament=self.tournament,
            group=self.group
        )
        
        # Create teams
        players = [
            Player.objects.create(first_name=f"P{i}", last_name=f"L{i}")
            for i in range(4)
        ]
        self.team1 = Team.objects.create(
            player1=players[0], player2=players[1],
            tournament_group=self.tournament_group
        )
        self.team2 = Team.objects.create(
            player1=players[2], player2=players[3],
            tournament_group=self.tournament_group
        )

    def test_match_result_calculation(self):
        match = Match.objects.create(
            tournament=self.tournament,
            team1=self.team1, team2=self.team2,
            set1_team1=6, set1_team2=4,
            set2_team1=6, set2_team2=3
        )
        
        service = MatchResultService()
        result = service.get_match_result(match)
        
        self.assertEqual(result['winner'], self.team1)
        self.assertEqual(result['sets_won'], {'team1': 2, 'team2': 0})
        self.assertEqual(result['points'], {'team1': 4, 'team2': 1})

    def test_match_with_third_set(self):
        match = Match.objects.create(
            tournament=self.tournament,
            team1=self.team1, team2=self.team2,
            set1_team1=6, set1_team2=4,
            set2_team1=4, set2_team2=6,
            set3_team1=7, set3_team2=5
        )
        
        service = MatchResultService()
        result = service.get_match_result(match)
        
        self.assertEqual(result['winner'], self.team1)
        self.assertEqual(result['sets_won'], {'team1': 2, 'team2': 1})


class StandingsCalculatorTest(TestCase):
    def setUp(self):
        self.tournament = Tournament.objects.create(
            name="Standings Test",
            start_date=date.today()
        )
        self.group = Group.objects.create(name="Test Group")
        self.tournament_group = TournamentGroup.objects.create(
            tournament=self.tournament,
            group=self.group
        )

    def test_empty_standings(self):
        calculator = StandingsCalculator()
        standings = calculator.calculate_standings(self.tournament_group)
        self.assertEqual(len(standings), 0)

    def test_standings_with_matches(self):
        # Create teams and matches
        players = [
            Player.objects.create(first_name=f"P{i}", last_name=f"L{i}")
            for i in range(6)
        ]
        teams = [
            Team.objects.create(
                player1=players[i], player2=players[i+1],
                tournament_group=self.tournament_group
            )
            for i in range(0, 6, 2)
        ]
        
        # Create matches
        Match.objects.create(
            tournament=self.tournament,
            team1=teams[0], team2=teams[1],
            set1_team1=6, set1_team2=4,
            set2_team1=6, set2_team2=3
        )
        Match.objects.create(
            tournament=self.tournament,
            team1=teams[1], team2=teams[2],
            set1_team1=6, set1_team2=4,
            set2_team1=6, set2_team2=3
        )
        
        calculator = StandingsCalculator()
        standings = calculator.calculate_standings(self.tournament_group)
        
        self.assertEqual(len(standings), 3)
        self.assertEqual(standings[0]['team'], teams[1])  # Should be first
        self.assertEqual(standings[0]['total_points'], 5)  # Won 1, lost 1