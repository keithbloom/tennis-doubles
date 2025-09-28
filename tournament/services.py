# tournament/services.py
from django.db.models import (
    Q,
    Prefetch,
    F,
    Value,
    CharField,
    Case,
    When,
    IntegerField,
)
from django.db.models.functions import Concat
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from .models import Tournament, TournamentGroup, Team, Match


@dataclass
class MatchResult:
    """Encapsulates match result information"""

    winner: Optional[Team]
    sets_won: Dict[str, int]
    points: Dict[str, int]
    games_won: Dict[str, int]
    games_played: int


class MatchResultService:
    """Service for calculating match results and statistics"""

    def get_match_result(self, match: Match) -> Dict[str, MatchResult]:
        """Calculate comprehensive match result"""
        sets = self._get_sets(match)
        sets_won = self._calculate_sets_won(sets, match)
        winner = self._determine_winner(sets_won, match)
        points = self._calculate_points(sets_won, match)
        games = self._calculate_games(sets)

        return {
            "winner": winner,
            "sets_won": sets_won,
            "points": points,
            "games_won": games["games_won"],
            "total_games": games["total_games"],
        }

    def _get_sets(self, match: Match) -> List[tuple]:
        """Extract sets from match"""
        sets = [
            (match.set1_team1, match.set1_team2),
            (match.set2_team1, match.set2_team2),
        ]
        if match.set3_team1 is not None and match.set3_team2 is not None:
            sets.append((match.set3_team1, match.set3_team2))
        return sets

    def _calculate_sets_won(self, sets: List[tuple], match: Match = None) -> Dict[str, int]:
        """Calculate sets won by each team"""
        # Handle retirement matches - the non-retired team gets 2 sets
        if match and match.retired_team == 'team1':
            return {"team1": 0, "team2": 2}  # team2 wins (team1 retired)
        elif match and match.retired_team == 'team2':
            return {"team1": 2, "team2": 0}  # team1 wins (team2 retired)

        team1_sets = sum(1 for s in sets if s[0] > s[1])
        team2_sets = sum(1 for s in sets if s[1] > s[0])
        return {"team1": team1_sets, "team2": team2_sets}

    def _determine_winner(
        self, sets_won: Dict[str, int], match: Match
    ) -> Optional[Team]:
        """Determine match winner"""
        # Handle retirement matches - the non-retired team wins
        if match.retired_team == 'team1':
            return match.team2  # team2 wins because team1 retired
        elif match.retired_team == 'team2':
            return match.team1  # team1 wins because team2 retired

        if sets_won["team1"] > sets_won["team2"]:
            return match.team1
        elif sets_won["team2"] > sets_won["team1"]:
            return match.team2
        return None

    def _calculate_points(self, sets_won: Dict[str, int], match: Match = None) -> Dict[str, int]:
        """Calculate points for each team"""
        # Handle retirement matches - the non-retired team gets win points
        if match and match.retired_team == 'team1':
            return {"team1": 1, "team2": 4}  # team2 wins (team1 retired)
        elif match and match.retired_team == 'team2':
            return {"team1": 4, "team2": 1}  # team1 wins (team2 retired)

        # Base point for playing
        points = {"team1": 1, "team2": 1}

        # Points for sets won
        points["team1"] += sets_won["team1"]
        points["team2"] += sets_won["team2"]

        # Bonus point for match winner
        if sets_won["team1"] > sets_won["team2"]:
            points["team1"] += 1
        else:
            points["team2"] += 1

        return points

    def _calculate_games(self, sets: List[tuple]) -> Dict[str, Any]:
        """Calculate games statistics"""
        team1_games = sum(s[0] for s in sets)
        team2_games = sum(s[1] for s in sets)
        total_games = team1_games + team2_games

        return {
            "games_won": {"team1": team1_games, "team2": team2_games},
            "total_games": total_games,
        }


class StandingsCalculator:
    """Service for calculating tournament standings"""

    def __init__(self):
        self.match_service = MatchResultService()

    def calculate_standings(
        self, tournament_group: TournamentGroup
    ) -> List[Dict[str, Any]]:
        """Calculate standings for a tournament group"""
        teams = self._get_teams_with_matches(tournament_group)
        standings = []

        for team in teams:
            stats = self._calculate_team_stats(team, tournament_group.tournament_id)
            standings.append(stats)

        # Sort by points, then sets %, then games %
        standings.sort(
            key=lambda x: (
                x["total_points"],
                x["sets_win_percentage"],
                x["games_win_percentage"],
            ),
            reverse=True,
        )

        return standings

    def _get_teams_with_matches(self, tournament_group: TournamentGroup):
        """Get teams with prefetched matches"""
        return Team.objects.filter(tournament_group=tournament_group).prefetch_related(
            Prefetch(
                "team1_matches",
                queryset=Match.objects.filter(
                    tournament_id=tournament_group.tournament_id,
                    team1__tournament_group=tournament_group,
                ),
                to_attr="matches_as_team1",
            ),
            Prefetch(
                "team2_matches",
                queryset=Match.objects.filter(
                    tournament_id=tournament_group.tournament_id,
                    team2__tournament_group=tournament_group,
                ),
                to_attr="matches_as_team2",
            ),
        )

    def _calculate_team_stats(self, team: Team, tournament_id: int) -> Dict[str, Any]:
        """Calculate statistics for a single team"""
        stats = {
            "team": team,
            "total_points": 0,
            "matches_played": 0,
            "total_sets_played": 0,
            "total_sets_won": 0,
            "total_games_played": 0,
            "total_games_won": 0,
            "sets_win_percentage": 0,
            "games_win_percentage": 0,
        }

        # Process matches as team1
        for match in team.matches_as_team1:
            result = self.match_service.get_match_result(match)
            self._update_stats_from_match(stats, result, "team1")
            stats["matches_played"] += 1

        # Process matches as team2
        for match in team.matches_as_team2:
            result = self.match_service.get_match_result(match)
            self._update_stats_from_match(stats, result, "team2")
            stats["matches_played"] += 1

        # Calculate percentages
        if stats["total_sets_played"] > 0:
            stats["sets_win_percentage"] = (
                stats["total_sets_won"] / stats["total_sets_played"] * 100
            )

        if stats["total_games_played"] > 0:
            stats["games_win_percentage"] = (
                stats["total_games_won"] / stats["total_games_played"] * 100
            )

        return stats

    def _update_stats_from_match(self, stats: Dict, result: Dict, team_position: str):
        """Update team statistics from a match result"""
        stats["total_points"] += result["points"][team_position]
        stats["total_sets_played"] += sum(result["sets_won"].values())
        stats["total_sets_won"] += result["sets_won"][team_position]
        stats["total_games_played"] += result["total_games"]
        stats["total_games_won"] += result["games_won"][team_position]


class TournamentGridBuilder:
    """Service for building tournament grid data"""

    def __init__(self):
        self.standings_calculator = StandingsCalculator()

    def build_grid_data(self, tournament: Tournament) -> List[Dict[str, Any]]:
        """Build complete grid data for tournament"""
        tournament_groups = TournamentGroup.objects.filter(
            tournament=tournament
        ).select_related("group")

        group_data = []
        for tournament_group in tournament_groups:
            data = self._build_group_data(tournament_group, tournament)
            group_data.append(data)

        return group_data

    def _build_group_data(
        self, tournament_group: TournamentGroup, tournament: Tournament
    ) -> Dict[str, Any]:
        """Build data for a single group"""
        teams = list(tournament_group.teams.all().order_by("rank"))

        return {
            "group": tournament_group.group,
            "teams": teams,
            "match_grid": self._build_match_grid(teams, tournament),
            "matches": self._get_annotated_matches(tournament_group, tournament),
            "standings": self.standings_calculator.calculate_standings(
                tournament_group
            ),
        }

    def _build_match_grid(
        self, teams: List[Team], tournament: Tournament
    ) -> List[List]:
        """Build the match grid matrix"""
        match_grid = []

        for team1 in teams:
            row = [team1]
            for team2 in teams:
                if team1 == team2:
                    row.append(None)
                else:
                    cell_value = self._get_grid_cell_value(team1, team2, tournament)
                    row.append(cell_value)
            match_grid.append(row)

        return match_grid

    def _get_grid_cell_value(
        self, team1: Team, team2: Team, tournament: Tournament
    ) -> Any:
        """Get value for a grid cell"""
        if team2.is_withdrawn:
            return "W"

        try:
            match = Match.objects.get(
                Q(team1=team1, team2=team2) | Q(team1=team2, team2=team1),
                tournament=tournament,
            )
            score = match.get_score().split("-")
            return int(score[0]) if match.team1 == team1 else int(score[1])
        except Match.DoesNotExist:
            return " "

    def _get_annotated_matches(
        self, tournament_group: TournamentGroup, tournament: Tournament
    ):
        """Get matches with annotations for display"""
        return (
            Match.objects.filter(
                tournament=tournament, team1__tournament_group=tournament_group
            )
            .order_by("-date_played")
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
                    # For retirement matches, no set winners (avoid highlighting scores)
                    When(retired_team__isnull=False, then=Value("none")),
                    # Normal set winner logic
                    When(set1_team1__gt=F("set1_team2"), then=Value("team1")),
                    When(set1_team2__gt=F("set1_team1"), then=Value("team2")),
                    default=Value("tie"),
                    output_field=CharField(),
                ),
                set2_winner=Case(
                    # For retirement matches, no set winners (avoid highlighting scores)
                    When(retired_team__isnull=False, then=Value("none")),
                    # Normal set winner logic
                    When(set2_team1__gt=F("set2_team2"), then=Value("team1")),
                    When(set2_team2__gt=F("set2_team1"), then=Value("team2")),
                    default=Value("tie"),
                    output_field=CharField(),
                ),
                set3_winner=Case(
                    # For retirement matches, no set winners (avoid highlighting scores)
                    When(retired_team__isnull=False, then=Value("none")),
                    # Normal set winner logic
                    When(set3_team1__gt=F("set3_team2"), then=Value("team1")),
                    When(set3_team2__gt=F("set3_team1"), then=Value("team2")),
                    When(set3_team1__isnull=True, then=Value("not_played")),
                    default=Value("tie"),
                    output_field=CharField(),
                ),
                sets_won_team1=Case(
                    # For retirement matches, winner gets 2 sets, loser gets 0
                    When(retired_team="team2", then=2),  # team2 retired, team1 wins
                    When(retired_team="team1", then=0),  # team1 retired, team1 loses
                    # Normal set counting logic
                    default=Case(
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
                    output_field=IntegerField(),
                ),
                sets_won_team2=Case(
                    # For retirement matches, winner gets 2 sets, loser gets 0
                    When(retired_team="team1", then=2),  # team1 retired, team2 wins
                    When(retired_team="team2", then=0),  # team2 retired, team2 loses
                    # Normal set counting logic
                    default=Case(
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
                    output_field=IntegerField(),
                ),
            )
            .annotate(
                match_winner=Case(
                    # Handle retirement - the non-retired team wins
                    When(retired_team="team1", then=Value("team2")),  # team1 retired, team2 wins
                    When(retired_team="team2", then=Value("team1")),  # team2 retired, team1 wins
                    # Normal match logic based on sets
                    When(sets_won_team1__gt=F("sets_won_team2"), then=Value("team1")),
                    When(sets_won_team2__gt=F("sets_won_team1"), then=Value("team2")),
                    default=Value("tie"),
                    output_field=CharField(),
                ),
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
                "match_winner",
                "date_played",
                "sets_won_team1",
                "sets_won_team2",
                "retired_team",
            )
        )
