from django.test import TestCase
from django.core.exceptions import ValidationError
from tournament.models import Tournament, Group, TournamentGroup, Player, Team, Match
from datetime import date


class MatchModelTest(TestCase):
    def setUp(self):
        self.tournament = Tournament.objects.create(
            name="Model Test",
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

    def test_retirement_match_validation_skipped(self):
        """Test that retirement matches skip normal score validation"""
        # This would normally fail validation due to no clear winner
        match = Match(
            tournament=self.tournament,
            team1=self.team1, team2=self.team2,
            set1_team1=6, set1_team2=6,  # Tied set - normally invalid
            set2_team1=4, set2_team2=4,  # Tied set - normally invalid
            retired_team='team2'  # team2 retired, so team1 wins
        )

        # Should not raise ValidationError because retirement skips validation
        try:
            match.clean()
        except ValidationError:
            self.fail("Retirement match should skip score validation")

    def test_normal_match_validation_still_works(self):
        """Test that normal matches still have proper validation"""
        match = Match(
            tournament=self.tournament,
            team1=self.team1, team2=self.team2,
            set1_team1=6, set1_team2=6,  # Tied set - should be invalid
            set2_team1=4, set2_team2=4   # Tied set - should be invalid
        )

        # Should raise ValidationError for tied sets
        with self.assertRaises(ValidationError):
            match.clean()

    def test_retired_team_choices(self):
        """Test retired team field accepts valid choices"""
        # Test team1 retired (team2 wins)
        match1 = Match.objects.create(
            tournament=self.tournament,
            team1=self.team1, team2=self.team2,
            set1_team1=0, set1_team2=0,
            set2_team1=0, set2_team2=0,
            retired_team='team1'
        )
        self.assertEqual(match1.retired_team, 'team1')

        # Test team2 retired (team1 wins)
        match2 = Match.objects.create(
            tournament=self.tournament,
            team1=self.team1, team2=self.team2,
            set1_team1=0, set1_team2=0,
            set2_team1=0, set2_team2=0,
            retired_team='team2'
        )
        self.assertEqual(match2.retired_team, 'team2')

        # Test no retirement
        match3 = Match.objects.create(
            tournament=self.tournament,
            team1=self.team1, team2=self.team2,
            set1_team1=6, set1_team2=4,
            set2_team1=6, set2_team2=3,
            retired_team=None
        )
        self.assertIsNone(match3.retired_team)

    def test_retirement_get_score_method(self):
        """Test that get_score returns correct values for retirement matches"""
        # Team2 retired (team1 wins)
        match1 = Match.objects.create(
            tournament=self.tournament,
            team1=self.team1, team2=self.team2,
            set1_team1=0, set1_team2=0,
            set2_team1=0, set2_team2=0,
            retired_team='team2'
        )
        self.assertEqual(match1.get_score(), "4-1")  # team1 wins

        # Team1 retired (team2 wins)
        match2 = Match.objects.create(
            tournament=self.tournament,
            team1=self.team1, team2=self.team2,
            set1_team1=0, set1_team2=0,
            set2_team1=0, set2_team2=0,
            retired_team='team1'
        )
        self.assertEqual(match2.get_score(), "1-4")  # team2 wins

        # Normal match (no retirement)
        match3 = Match.objects.create(
            tournament=self.tournament,
            team1=self.team1, team2=self.team2,
            set1_team1=6, set1_team2=4,
            set2_team1=6, set2_team2=3
        )
        self.assertEqual(match3.get_score(), "4-1")  # 1 + 2 sets + 1 bonus vs 1 point