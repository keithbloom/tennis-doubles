from django.shortcuts import render
from django.db.models import Q, Prefetch
from .models import Group, Match, Team
from django.db.models import F, Value, CharField, Case, When, IntegerField
from django.db.models import (
    Sum, Count, Subquery, OuterRef
)
from django.db.models.functions import Concat, Round
import logging

logger = logging.getLogger(__name__)


def tournament_grid(request):
    groups = Group.objects.prefetch_related("teams").all()
    group_data = []
    for group in groups:
        teams = list(group.teams.all().order_by("rank"))
        match_grid = []
        someMatches = (
            Match.objects.order_by('-date_played').filter(team1__group=group)
            .annotate(
                team1_name=Concat(
                    F("team1__player1__first_name"),
                    Value("/"),
                    F("team1__player2__first_name"),
                    output_field=CharField(),
                ),
                team2_name=Concat(
                    F("team2__player1__first_name"),
                    Value("/"),
                    F("team2__player2__first_name"),
                    output_field=CharField(),
                ),
                set1_winner=Case(
                    When(set1_team1__gt=F("set1_team2"), then=Value("team1")),
                    When(set1_team2__gt=F("set1_team1"), then=Value("team2")),
                    default=Value("tie"),
                    output_field=CharField(),
                ),
                set2_winner=Case(
                    When(set2_team1__gt=F("set2_team2"), then=Value("team1")),
                    When(set2_team2__gt=F("set2_team1"), then=Value("team2")),
                    default=Value("tie"),
                    output_field=CharField(),
                ),
                set3_winner=Case(
                    When(set3_team1__gt=F("set3_team2"), then=Value("team1")),
                    When(set3_team2__gt=F("set3_team1"), then=Value("team2")),
                    When(set3_team1__isnull=True, then=Value("not_played")),
                    default=Value("tie"),
                    output_field=CharField(),
                ),
                sets_won_team1=Case(
                    When(set1_team1__gt=F("set1_team2"), then=1),
                    default=0,
                    output_field=IntegerField(),
                )
                + Case(
                    When(set2_team1__gt=F("set2_team2"), then=1),
                    default=0,
                    output_field=IntegerField(),
                )
                + Case(
                    When(set3_team1__gt=F("set3_team2"), then=1),
                    default=0,
                    output_field=IntegerField(),
                ),
                sets_won_team2=Case(
                    When(set1_team2__gt=F("set1_team1"), then=1),
                    default=0,
                    output_field=IntegerField(),
                )
                + Case(
                    When(set2_team2__gt=F("set2_team1"), then=1),
                    default=0,
                    output_field=IntegerField(),
                )
                + Case(
                    When(set3_team2__gt=F("set3_team1"), then=1),
                    default=0,
                    output_field=IntegerField(),
                ),
            )
            .annotate(
                match_winner=Case(
                    When(sets_won_team1__gt=F("sets_won_team2"), then=Value("team1")),
                    When(sets_won_team2__gt=F("sets_won_team1"), then=Value("team2")),
                    default=Value("tie"),
                    output_field=CharField(),
                )
            )
            .values(
                "id",
                "team1_name",
                "team2_name",
                "set1_team1",
                "set1_team2",
                "set2_team1",
                "set2_team2",
                "set3_team1",
                "set3_team2",
                "set1_winner",
                "set2_winner",
                "set3_winner",
                "sets_won_team1",
                "sets_won_team2",
                "match_winner",
                "date_played",
            )
        )
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

        group_data.append(
            {
                "group": group,
                "teams": teams,
                "match_grid": match_grid,
                "matches": someMatches,
            }
        )
        
    context = {"group_data": group_data}
    return render(request, "tournament/grid.html", context)

def get_standings(group_id):
    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        return f"Group with id {group_id} does not exist."

    # Prefetch matches for each team in the group
    team_prefetch1 = Prefetch(
        'team1_matches',
        queryset=Match.objects.filter(team1__group_id=group_id),
        to_attr='matches_as_team1'
    )
    team_prefetch2 = Prefetch(
        'team2_matches',
        queryset=Match.objects.filter(team2__group_id=group_id),
        to_attr='matches_as_team2'
    )

    # Fetch teams with their matches
    teams = Team.objects.filter(group_id=group_id).prefetch_related(team_prefetch1, team_prefetch2)

    # Process data for each team
    standings = []
    for team in teams:
        total_points = 0
        total_sets_played = 0
        total_sets_won = 0
        total_games_played = 0
        total_games_won = 0
        matches_played = 0
        
        # Process matches where the team is team1
        for match in team.matches_as_team1:
            score = match.get_score()
            total_points += int(score.split('-')[0])
            # Always play at least 2 sets
            total_sets_played += 2 + (1 if match.set3_team1 is not None else 0)
            total_sets_won += (match.set1_team1 > match.set1_team2) + (match.set2_team1 > match.set2_team2)
            if match.set3_team1 is not None:
                total_sets_won += (match.set3_team1 > match.set3_team2)
            total_games_played += match.set1_team1 + match.set1_team2 + match.set2_team1 + match.set2_team2
            total_games_won += match.set1_team1 + match.set2_team1
            matches_played += 1

        # Process matches where the team is team2
        for match in team.matches_as_team2:
            score = match.get_score()
            total_points += int(score.split('-')[1])
            # Always play at least 2 sets
            total_sets_played += 2 + (1 if match.set3_team2 is not None else 0)
            total_sets_won += (match.set1_team2 > match.set1_team1) + (match.set2_team2 > match.set2_team1)
            if match.set3_team2 is not None:
                total_sets_won += (match.set3_team2 > match.set3_team1)
            total_games_played += match.set1_team1 + match.set1_team2 + match.set2_team1 + match.set2_team2
            total_games_won += match.set1_team2 + match.set2_team2
            matches_played += 1

        standings.append({
            'team': team,
            'total_points': total_points,
            'matches_played': matches_played,
            'total_sets_played': total_sets_played,
            'total_sets_won': total_sets_won,
            'sets_win_percentage': (total_sets_won / total_sets_played * 100) if total_sets_played > 0 else 0,
            'total_games_played': total_games_played,
            'total_games_won': total_games_won,
            'games_win_percentage': (total_games_won / total_games_played * 100) if total_games_played > 0 else 0
        
        })

    # Sort standings by total points (descending)
    standings.sort(key=lambda x: (x['total_points'], x['sets_win_percentage'], x['games_win_percentage']), reverse=True)


    return standings

def test_standings(id):
    standings = get_standings(id)
    for rank, stat in enumerate(standings, start=1):
        print(f"Rank: {rank}")
        print(f"Team: {stat['team']}")
        print(f"Total Points: {stat['total_points']}")
        print(f"Matches Played: {stat['matches_played']}")
        print(f"Total Sets Played: {stat['total_sets_played']}")
        print(f"Total Sets Won: {stat['total_sets_won']}")
        print(f"Sets Win Percentage: {stat['sets_win_percentage']:.2f}%")
        print(f"Total Games Played: {stat['total_games_played']}")
        print(f"Total Games Won: {stat['total_games_won']}")
        print("---")