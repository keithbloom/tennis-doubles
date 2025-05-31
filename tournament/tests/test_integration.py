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