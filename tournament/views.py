from django.shortcuts import render
from django.db.models import Q
from .models import Group, Match
from django.db.models import F, Value, CharField, Case, When, IntegerField
from django.db.models.functions import Concat
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
