# tournament/views.py
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required 
from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView
from .models import Tournament, Match
from .services import TournamentGridBuilder, StandingsCalculator
from .api import TeamAPI
import logging

logger = logging.getLogger(__name__)


class TournamentGridView(TemplateView):
    """View for displaying tournament grid"""
    template_name = "tournament/grid.html"
    
    def get_template_names(self):
        """Return template name based on tournament existence"""
        tournament = Tournament.objects.filter(
            status='ONGOING',
            end_date__isnull=True
        ).order_by('-start_date').first()
        
        if not tournament:
            return ["tournament/no_tournament.html"]
        return [self.template_name]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get latest ongoing tournament
        tournament = Tournament.objects.filter(
            status='ONGOING',
            end_date__isnull=True
        ).order_by('-start_date').first()
        
        if not tournament:
            return context
            
        # Use service to build grid data
        grid_builder = TournamentGridBuilder()
        context['group_data'] = grid_builder.build_grid_data(tournament)
        context['matches'] = Match.objects.filter(
            tournament=tournament
        ).select_related('team1', 'team2')
        
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
            id=tournament_group_id,
            tournament_id=tournament_id
        )
    except TournamentGroup.DoesNotExist:
        return f"Tournament group with id {tournament_group_id} does not exist."
    
    calculator = StandingsCalculator()
    return calculator.calculate_standings(tournament_group)


@staff_member_required
def teams_by_tournament(request):
    """API endpoint for getting teams by tournament"""
    tournament_id = request.GET.get('tournament')
    if not tournament_id:
        return JsonResponse({'error': 'Tournament ID required'}, status=400)
    
    api = TeamAPI()
    teams_data = api.get_teams_by_tournament(tournament_id)
    return JsonResponse(teams_data, safe=False)