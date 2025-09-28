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

    def test_retirement_team2_retired(self):
        # team2 retired, so team1 wins
        match = Match.objects.create(
            tournament=self.tournament,
            team1=self.team1, team2=self.team2,
            set1_team1=0, set1_team2=0,
            set2_team1=0, set2_team2=0,
            retired_team='team2'
        )

        service = MatchResultService()
        result = service.get_match_result(match)

        self.assertEqual(result['winner'], self.team1)
        self.assertEqual(result['sets_won'], {'team1': 2, 'team2': 0})
        self.assertEqual(result['points'], {'team1': 4, 'team2': 1})

    def test_retirement_team1_retired(self):
        # team1 retired, so team2 wins
        match = Match.objects.create(
            tournament=self.tournament,
            team1=self.team1, team2=self.team2,
            set1_team1=0, set1_team2=0,
            set2_team1=0, set2_team2=0,
            retired_team='team1'
        )

        service = MatchResultService()
        result = service.get_match_result(match)

        self.assertEqual(result['winner'], self.team2)
        self.assertEqual(result['sets_won'], {'team1': 0, 'team2': 2})
        self.assertEqual(result['points'], {'team1': 1, 'team2': 4})

    def test_match_get_score_retirement(self):
        # Test team2 retired (team1 wins)
        match1 = Match.objects.create(
            tournament=self.tournament,
            team1=self.team1, team2=self.team2,
            set1_team1=0, set1_team2=0,
            set2_team1=0, set2_team2=0,
            retired_team='team2'
        )
        self.assertEqual(match1.get_score(), "4-1")

        # Test team1 retired (team2 wins)
        match2 = Match.objects.create(
            tournament=self.tournament,
            team1=self.team1, team2=self.team2,
            set1_team1=0, set1_team2=0,
            set2_team1=0, set2_team2=0,
            retired_team='team1'
        )
        self.assertEqual(match2.get_score(), "1-4")


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

    def test_standings_with_retirement_matches(self):
        """Test standings calculation includes retirement matches correctly"""
        # Create teams and players
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

        # Create normal match: teams[0] beats teams[1]
        Match.objects.create(
            tournament=self.tournament,
            team1=teams[0], team2=teams[1],
            set1_team1=6, set1_team2=4,
            set2_team1=6, set2_team2=3
        )

        # Create retirement match: teams[2] retired, so teams[0] wins
        Match.objects.create(
            tournament=self.tournament,
            team1=teams[0], team2=teams[2],
            set1_team1=0, set1_team2=0,
            set2_team1=0, set2_team2=0,
            retired_team='team2'  # teams[2] retired
        )

        calculator = StandingsCalculator()
        standings = calculator.calculate_standings(self.tournament_group)

        self.assertEqual(len(standings), 3)

        # teams[0] should be first with 8 points (4 from normal win + 4 from retirement win)
        self.assertEqual(standings[0]['team'], teams[0])
        self.assertEqual(standings[0]['total_points'], 8)

        # teams[1] and teams[2] should each have 1 point (participation point)
        team1_standing = next(s for s in standings if s['team'] == teams[1])
        team2_standing = next(s for s in standings if s['team'] == teams[2])
        self.assertEqual(team1_standing['total_points'], 1)
        self.assertEqual(team2_standing['total_points'], 1)