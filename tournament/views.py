# tournament/views.py
from datetime import datetime
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic import TemplateView
from .models import Tournament
from .services import TournamentGridBuilder, StandingsCalculator
from .api import TeamAPI
import logging

logger = logging.getLogger(__name__)


class TournamentGridView(TemplateView):
    """View for displaying tournament grid"""

    template_name = "tournament/grid.html"

    def get_template_names(self):
        """Return template name based on tournament existence"""
        tournament = (
            Tournament.objects.filter(status="ONGOING", end_date__isnull=True, start_date__lte=datetime.now())
            .order_by("-start_date")
            .first()
        )

        if not tournament:
            return ["tournament/no_tournament.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get latest ongoing tournament
        tournament = (
            Tournament.objects.filter(status="ONGOING", end_date__isnull=True)
            .order_by("-start_date")
            .first()
        )

        if not tournament:
            return context

        # Pass tournament object for header and navigation
        context["tournament"] = tournament

        # Use service to build grid data
        grid_builder = TournamentGridBuilder()
        context["group_data"] = grid_builder.build_grid_data(tournament)

        # Add prev/next tournament IDs for navigation (only if viewing current)
        context["prev_tournament"] = None
        context["next_tournament"] = None

        return context


# For backwards compatibility, keep the function-based view
def tournament_grid(request):
    """Function-based view wrapper for TournamentGridView"""
    view = TournamentGridView.as_view()
    return view(request)


def get_standings(tournament_id, tournament_group_id):
    """Get standings for a tournament group"""
    from .models import TournamentGroup

    try:
        tournament_group = TournamentGroup.objects.get(
            id=tournament_group_id, tournament_id=tournament_id
        )
    except TournamentGroup.DoesNotExist:
        return f"Tournament group with id {tournament_group_id} does not exist."

    calculator = StandingsCalculator()
    return calculator.calculate_standings(tournament_group)


class TournamentDetailView(TemplateView):
    """View for displaying a specific tournament grid"""

    template_name = "tournament/grid.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        tournament_id = self.kwargs.get('tournament_id')

        try:
            tournament = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            from django.http import Http404
            raise Http404("Tournament not found")

        # Pass tournament object
        context["tournament"] = tournament

        # Use service to build grid data
        grid_builder = TournamentGridBuilder()
        context["group_data"] = grid_builder.build_grid_data(tournament)

        # Add prev/next tournament IDs for navigation
        prev_tournament = (
            Tournament.objects.filter(start_date__lt=tournament.start_date)
            .order_by('-start_date')
            .first()
        )
        next_tournament = (
            Tournament.objects.filter(start_date__gt=tournament.start_date)
            .order_by('start_date')
            .first()
        )

        context["prev_tournament"] = prev_tournament
        context["next_tournament"] = next_tournament

        return context


class TournamentHistoryView(TemplateView):
    """View for displaying list of all tournaments"""

    template_name = "tournament/history.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all tournaments in reverse chronological order
        tournaments = Tournament.objects.all().order_by('-start_date')

        context["tournaments"] = tournaments

        return context


@staff_member_required
def teams_by_tournament(request):
    """API endpoint for getting teams by tournament"""
    tournament_id = request.GET.get("tournament")
    if not tournament_id:
        return JsonResponse({"error": "Tournament ID required"}, status=400)

    api = TeamAPI()
    teams_data = api.get_teams_by_tournament(tournament_id)
    return JsonResponse(teams_data, safe=False)


@staff_member_required
def previous_partner(request):
    """API endpoint for getting a player's previous partner"""
    player_id = request.GET.get("player_id")

    if not player_id:
        return JsonResponse({"error": "player_id required"}, status=400)

    api = TeamAPI()
    partner_id = api.get_previous_partner(int(player_id))

    return JsonResponse({"partner_id": partner_id})
