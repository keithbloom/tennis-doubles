from django.shortcuts import render
from django.db.models import Q
from .models import Group, Match

import logging

logger = logging.getLogger(__name__)


def tournament_grid(request):
    groups = Group.objects.prefetch_related("teams").all()

    group_data = []
    for group in groups:
        teams = list(
            group.teams.all().order_by("rank")
        )
        match_grid = []
        for team1 in teams:
            row = [team1]
            for team2 in teams:
                if team1 == team2:
                    row.append(None)  # This will be grayed out in the template
                else:
                    try:
                        match = Match.objects.get(
                            Q(team1=team1, team2=team2) | Q(team1=team2, team2=team1)
                        )
                        # Calculate points for team1 in this match
                        score = match.get_score().split("-")
                        points = (
                            int(score[0]) if match.team1 == team1 else int(score[1])
                        )
                        row.append(points)
                    except Match.DoesNotExist:
                        row.append(" ")  # No match played yet
            match_grid.append(row)

        group_data.append({"group": group, "teams": teams, "match_grid": match_grid})
        matches = [
        {
            'team1_player1': 'Lucy',
            'team1_player2': 'Susan',
            'team2_player1': 'Ainoha',
            'team2_player2': 'Hannah',
            'set1_team1': 6,
            'set2_team1': 6,
            'set3_team1': None,
            'set1_team2': 4,
            'set2_team2': 4,
            'set3_team2': None,
            'team1_winner': True
        },
        # Add more match dictionaries here...
    ]

    context = {"group_data": group_data, "matches": matches}
    return render(request, "tournament/grid.html", context)
