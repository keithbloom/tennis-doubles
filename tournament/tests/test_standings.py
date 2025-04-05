from django.test import TransactionTestCase
from django.core.exceptions import ValidationError
from tournament.models import Player, Group, Team, Match, Tournament, TournamentGroup
from tournament.views import get_standings

class GetStandingsTestCase(TransactionTestCase):
    def setUp(self):
        # Create a test tournament
        self.tournament = Tournament.objects.create(
            name="Test Tournament", 
            start_date="2024-01-01"
        )
        
        # Create a test group
        self.group = Group.objects.create(name="Test Group")
        
        # Create tournament group
        self.tournament_group = TournamentGroup.objects.create(
            tournament=self.tournament,
            group=self.group
        )

        # Create test players
        self.player1 = Player.objects.create(first_name="Player1", last_name="One")
        self.player2 = Player.objects.create(first_name="Player2", last_name="Two")
        self.player3 = Player.objects.create(first_name="Player3", last_name="Three")
        self.player4 = Player.objects.create(first_name="Player4", last_name="Four")

        # Create test teams
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

    def tearDown(self):
        # Clean up all created objects
        Match.objects.all().delete()
        Team.objects.all().delete()
        TournamentGroup.objects.all().delete()
        Player.objects.all().delete()
        Group.objects.all().delete()
        Tournament.objects.all().delete()

    def test_tournament_group_not_found(self):
        # Test when the tournament group doesn't exist
        result = get_standings(self.tournament.id, 999)
        self.assertEqual(result, f"Tournament group with id 999 does not exist.")

    def test_empty_group(self):
        # Test when the group has no matches
        standings = get_standings(self.tournament.id, self.tournament_group.id)
        self.assertEqual(len(standings), 2)
        for standing in standings:
            self.assertEqual(standing['total_points'], 0)
            self.assertEqual(standing['matches_played'], 0)
            self.assertEqual(standing['total_sets_played'], 0)
            self.assertEqual(standing['total_sets_won'], 0)
            self.assertEqual(standing['total_games_played'], 0)
            self.assertEqual(standing['total_games_won'], 0)
            self.assertEqual(standing['sets_win_percentage'], 0)
            self.assertEqual(standing['games_win_percentage'], 0)

    def test_single_match_two_sets(self):
        # Test with a single match of two sets
        Match.objects.create(
            tournament=self.tournament,
            team1=self.team1, 
            team2=self.team2,
            set1_team1=6, 
            set1_team2=4,
            set2_team1=6, 
            set2_team2=3
        )
        standings = get_standings(self.tournament.id, self.tournament_group.id)
        self.assertEqual(len(standings), 2)
        
        # Check team1 stats
        team1_standing = next(s for s in standings if s['team'] == self.team1)
        self.assertEqual(team1_standing['total_points'], 4)  # 1 for playing, 1 for each set, 1 for winning
        self.assertEqual(team1_standing['matches_played'], 1)
        self.assertEqual(team1_standing['total_sets_played'], 2)
        self.assertEqual(team1_standing['total_sets_won'], 2)
        self.assertEqual(team1_standing['total_games_played'], 19)
        self.assertEqual(team1_standing['total_games_won'], 12)
        self.assertAlmostEqual(team1_standing['sets_win_percentage'], 100)
        self.assertAlmostEqual(team1_standing['games_win_percentage'], 63.16, places=2)

        # Check team2 stats
        team2_standing = next(s for s in standings if s['team'] == self.team2)
        self.assertEqual(team2_standing['total_points'], 1)  # 1 for playing
        self.assertEqual(team2_standing['matches_played'], 1)
        self.assertEqual(team2_standing['total_sets_played'], 2)
        self.assertEqual(team2_standing['total_sets_won'], 0)
        self.assertEqual(team2_standing['total_games_played'], 19)
        self.assertEqual(team2_standing['total_games_won'], 7)
        self.assertEqual(team2_standing['sets_win_percentage'], 0)
        self.assertAlmostEqual(team2_standing['games_win_percentage'], 36.84, places=2)

    def test_single_match_three_sets(self):
        # Test with a single match of three sets
        Match.objects.create(
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
        standings = get_standings(self.tournament.id, self.tournament_group.id)
        
        # Check team1 stats
        team1_standing = next(s for s in standings if s['team'] == self.team1)
        self.assertEqual(team1_standing['total_points'], 4)  # 1 for playing, 1 for each set won, 1 for winning
        self.assertEqual(team1_standing['total_sets_played'], 3)
        self.assertEqual(team1_standing['total_sets_won'], 2)

    def test_multiple_matches(self):
        # Test with multiple matches
        Match.objects.create(
            tournament=self.tournament,
            team1=self.team1, 
            team2=self.team2,
            set1_team1=6, 
            set1_team2=4,
            set2_team1=6, 
            set2_team2=3
        )
        Match.objects.create(
            tournament=self.tournament,
            team1=self.team2, 
            team2=self.team1,
            set1_team1=7, 
            set1_team2=5,
            set2_team1=6, 
            set2_team2=4
        )
        standings = get_standings(self.tournament.id, self.tournament_group.id)
        
        # Both teams should have played 2 matches
        for standing in standings:
            self.assertEqual(standing['matches_played'], 2)
            self.assertEqual(standing['total_sets_played'], 4)

    def test_sorting(self):
        # Test that standings are sorted correctly
        player5 = Player.objects.create(first_name="Player", last_name="Five")
        player6 = Player.objects.create(first_name="Player", last_name="Six")
        team3 = Team.objects.create(
            player1=player5, 
            player2=player6, 
            tournament_group=self.tournament_group
        )
        Match.objects.create(
            tournament=self.tournament,
            team1=self.team1, 
            team2=self.team2,
            set1_team1=6, 
            set1_team2=4,
            set2_team1=6, 
            set2_team2=3
        )
        Match.objects.create(
            tournament=self.tournament,
            team1=self.team2, 
            team2=team3,
            set1_team1=6, 
            set1_team2=4,
            set2_team1=6, 
            set2_team2=3
        )
        standings = get_standings(self.tournament.id, self.tournament_group.id)

        # Team1 and Team2 should have more points than Team3
        self.assertEqual(standings[0]['team'], self.team2)
        self.assertEqual(standings[1]['team'], self.team1)
        self.assertEqual(standings[2]['team'], team3)

    def test_get_score_method(self):
        # Test that the get_score method is used correctly
        match = Match.objects.create(
            tournament=self.tournament,
            team1=self.team1, 
            team2=self.team2,
            set1_team1=6, 
            set1_team2=4,
            set2_team1=6, 
            set2_team2=3
        )
        standings = get_standings(self.tournament.id, self.tournament_group.id)
        
        team1_standing = next(s for s in standings if s['team'] == self.team1)
        expected_score = match.get_score().split('-')[0]
        self.assertEqual(team1_standing['total_points'], int(expected_score))

    def test_team_validation(self):
        # Test that a team cannot be created with the same player twice
        with self.assertRaises(ValidationError):
            Team.objects.create(
                player1=self.player1, 
                player2=self.player1, 
                tournament_group=self.tournament_group
            )

    def test_match_validation(self):
        # Test that a match cannot be created with teams from different tournament groups
        other_group = Group.objects.create(name="Other Group")
        other_tournament_group = TournamentGroup.objects.create(
            tournament=self.tournament,
            group=other_group
        )
        player7 = Player.objects.create(first_name="Player", last_name="Seven")
        player8 = Player.objects.create(first_name="Player", last_name="Eight")
        team3 = Team.objects.create(
            player1=player7, 
            player2=player8, 
            tournament_group=other_tournament_group
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