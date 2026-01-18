from typing import List, Dict, Any, Optional
from django.db.models import QuerySet, Q
from .models import Team, Tournament


class TeamAPI:
    """API service for team-related operations"""

    def get_teams_by_tournament(self, tournament_id: int) -> List[Dict[str, Any]]:
        """Get teams grouped by tournament group"""
        teams = Team.objects.filter(
            tournament_group__tournament_id=tournament_id
        ).select_related(
            'player1', 'player2',
            'tournament_group', 'tournament_group__group'
        ).order_by('tournament_group__group__name')

        return self._group_teams_by_tournament_group(teams)

    def _group_teams_by_tournament_group(self, teams: QuerySet) -> List[Dict[str, Any]]:
        """Group teams by their tournament group"""
        groups_dict = {}

        for team in teams:
            group_name = team.tournament_group.group.name
            if group_name not in groups_dict:
                groups_dict[group_name] = {
                    'id': team.tournament_group.id,
                    'name': group_name,
                    'teams': []
                }

            groups_dict[group_name]['teams'].append({
                'id': team.id,
                'name': f"{team.player1.first_name}/{team.player2.first_name}"
            })

        return list(groups_dict.values())

    def get_previous_partner(self, player_id: int) -> Optional[int]:
        """Get the player's partner from the most recent completed tournament"""
        # Find the most recent completed tournament
        previous_tournament = Tournament.objects.filter(
            status='COMPLETED'
        ).order_by('-start_date').first()

        if not previous_tournament:
            return None

        # Find the team this player was on in the previous tournament
        previous_team = Team.objects.filter(
            tournament_group__tournament=previous_tournament
        ).filter(
            Q(player1_id=player_id) | Q(player2_id=player_id)
        ).first()

        if not previous_team:
            return None

        # Return the partner's ID (the other player on the team)
        if previous_team.player1_id == player_id:
            return previous_team.player2_id
        else:
            return previous_team.player1_id