from django.test import TransactionTestCase
from tournament.models import Tournament, Group, TournamentGroup, Player, Team, Match
from datetime import date

class TournamentIntegrationTest(TransactionTestCase):
    """Integration tests for the tournament system"""
    
    def setUp(self):
        """Ensure clean state before each test"""
        # Clear any existing tournaments to avoid conflicts
        Tournament.objects.all().delete()
    
    def test_complete_tournament_flow(self):
        """Test a complete tournament flow from creation to standings"""
        # Ensure no other ONGOING tournaments exist
        Tournament.objects.filter(status='ONGOING').delete()
        
        # Create tournament
        tournament = Tournament.objects.create(
            name="Integration Test Tournament",
            start_date=date.today(),
            status="ONGOING"
        )
        
        # Create groups
        group_a = Group.objects.create(name="Group A")
        group_b = Group.objects.create(name="Group B")
        
        # Create tournament groups
        tg_a = TournamentGroup.objects.create(tournament=tournament, group=group_a)
        tg_b = TournamentGroup.objects.create(tournament=tournament, group=group_b)
        
        # Create players
        players = []
        for i in range(8):
            player = Player.objects.create(
                first_name=f"Player{i+1}",
                last_name=f"Last{i+1}"
            )
            players.append(player)
        
        # Create teams for Group A
        team_a1 = Team.objects.create(
            player1=players[0], player2=players[1],
            tournament_group=tg_a, rank=1
        )
        team_a2 = Team.objects.create(
            player1=players[2], player2=players[3],
            tournament_group=tg_a, rank=2
        )
        
        # Create teams for Group B
        team_b1 = Team.objects.create(
            player1=players[4], player2=players[5],
            tournament_group=tg_b, rank=1
        )
        team_b2 = Team.objects.create(
            player1=players[6], player2=players[7],
            tournament_group=tg_b, rank=2
        )
        
        # Create matches
        match_a = Match.objects.create(
            tournament=tournament,
            team1=team_a1, team2=team_a2,
            set1_team1=6, set1_team2=4,
            set2_team1=6, set2_team2=3
        )
        
        match_b = Match.objects.create(
            tournament=tournament,
            team1=team_b1, team2=team_b2,
            set1_team1=4, set1_team2=6,
            set2_team1=3, set2_team2=6
        )
        
        # Test tournament grid view
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Check that both groups are displayed
        self.assertContains(response, "Group A")
        self.assertContains(response, "Group B")
        
        # Check that all players are displayed
        for player in players:
            self.assertContains(response, player.first_name)
        
        # Check match scores are displayed
        self.assertContains(response, "6")
        self.assertContains(response, "4")
        self.assertContains(response, "3")

    def test_retirement_integration_flow(self):
        """Test complete retirement flow including display"""
        # Ensure no other ONGOING tournaments exist
        Tournament.objects.filter(status='ONGOING').delete()

        # Create tournament setup
        tournament = Tournament.objects.create(
            name="Retirement Test Tournament",
            start_date=date.today(),
            status="ONGOING"
        )

        group = Group.objects.create(name="Test Group")
        group2 = Group.objects.create(name="Test Group 2")
        tg = TournamentGroup.objects.create(tournament=tournament, group=group)
        TournamentGroup.objects.create(tournament=tournament, group=group2)

        # Create players and teams
        players = [
            Player.objects.create(first_name=f"Player{i+1}", last_name=f"Last{i+1}")
            for i in range(6)
        ]

        team1 = Team.objects.create(
            player1=players[0], player2=players[1],
            tournament_group=tg, rank=1
        )
        team2 = Team.objects.create(
            player1=players[2], player2=players[3],
            tournament_group=tg, rank=2
        )
        team3 = Team.objects.create(
            player1=players[4], player2=players[5],
            tournament_group=tg, rank=3
        )

        # Create normal match
        normal_match = Match.objects.create(
            tournament=tournament,
            team1=team1, team2=team2,
            set1_team1=6, set1_team2=4,
            set2_team1=6, set2_team2=3
        )

        # Create retirement match - team3 retired, so team2 wins
        retirement_match = Match.objects.create(
            tournament=tournament,
            team1=team2, team2=team3,
            set1_team1=0, set1_team2=0,
            set2_team1=0, set2_team2=0,
            retired_team='team2'  # team2 is the retired team position (actually team3 retired)
        )

        # Test that retirement match has correct score
        self.assertEqual(retirement_match.get_score(), "4-1")  # team2 wins because team3 retired

        # Test tournament grid view includes retirement
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

        # Check that retired marker is displayed
        self.assertContains(response, "(Retired)")

        # Verify the match data in context to ensure correct winner determination
        context_data = response.context
        group_data = context_data['group_data'][0]
        matches = group_data['matches']

        # Find the retirement match
        retirement_match_data = next(
            (m for m in matches if m['retired_team'] == 'team2'), None
        )
        self.assertIsNotNone(retirement_match_data)

        # Verify that team1 (the non-retired team) is marked as the winner
        self.assertEqual(retirement_match_data['match_winner'], 'team1')  # team1 wins because team2 retired

        # Check that both normal and retirement matches are included
        self.assertContains(response, "Test Group")
        for player in players:
            self.assertContains(response, player.first_name)

    def test_retirement_standings_calculation(self):
        """Test that retirement matches are correctly included in standings"""
        # Ensure no other ONGOING tournaments exist
        Tournament.objects.filter(status='ONGOING').delete()

        tournament = Tournament.objects.create(
            name="Retirement Standings Test",
            start_date=date.today(),
            status="ONGOING"
        )

        group = Group.objects.create(name="Standings Group")
        group2 = Group.objects.create(name="Standings Group 2")
        tg = TournamentGroup.objects.create(tournament=tournament, group=group)
        TournamentGroup.objects.create(tournament=tournament, group=group2)

        # Create teams
        players = [
            Player.objects.create(first_name=f"Player{i+1}", last_name=f"Last{i+1}")
            for i in range(6)
        ]

        team1 = Team.objects.create(
            player1=players[0], player2=players[1],
            tournament_group=tg, rank=1
        )
        team2 = Team.objects.create(
            player1=players[2], player2=players[3],
            tournament_group=tg, rank=2
        )
        team3 = Team.objects.create(
            player1=players[4], player2=players[5],
            tournament_group=tg, rank=3
        )

        # Team1 beats Team2 normally
        Match.objects.create(
            tournament=tournament,
            team1=team1, team2=team2,
            set1_team1=6, set1_team2=4,
            set2_team1=6, set2_team2=3
        )

        # Team1 beats Team3 because Team3 retired
        Match.objects.create(
            tournament=tournament,
            team1=team1, team2=team3,
            set1_team1=0, set1_team2=0,
            set2_team1=0, set2_team2=0,
            retired_team='team2'  # team3 retired (team2 position)
        )

        # Test standings calculation
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

        # Team1 should have highest points (4 + 4 = 8 points)
        # Team2 should have 1 point (lost to team1)
        # Team3 should have 1 point (lost by retirement to team1)
        context_data = response.context
        group_data = context_data['group_data'][0]
        standings = group_data['standings']

        # Team1 should be first with 8 points
        self.assertEqual(standings[0]['team'], team1)
        self.assertEqual(standings[0]['total_points'], 8)