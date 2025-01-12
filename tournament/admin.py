from django.contrib import admin
from .models import Tournament, Group, TournamentGroup, Player, Team, Match

@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'status']
    list_filter = ['status']

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(TournamentGroup)
class TournamentGroupAdmin(admin.ModelAdmin):
    list_display = ['tournament', 'group']
    list_filter = ['tournament', 'group']

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name']
    search_fields = ['first_name', 'last_name']

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'player1', 'player2', 'get_group', 'get_tournament', 'rank']
    list_filter = ['tournament_group__group', 'tournament_group__tournament']
    search_fields = ['player1__first_name', 'player1__last_name', 
                    'player2__first_name', 'player2__last_name']

    def get_group(self, obj):
        return obj.tournament_group.group
    get_group.short_description = 'Group'
    get_group.admin_order_field = 'tournament_group__group'

    def get_tournament(self, obj):
        return obj.tournament_group.tournament
    get_tournament.short_description = 'Tournament'
    get_tournament.admin_order_field = 'tournament_group__tournament'

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'tournament', 'date_played', 'get_score']
    list_filter = ['tournament', 'team1__tournament_group__group', 'date_played']
    search_fields = ['team1__player1__first_name', 'team1__player1__last_name',
                    'team1__player2__first_name', 'team1__player2__last_name',
                    'team2__player1__first_name', 'team2__player1__last_name',
                    'team2__player2__first_name', 'team2__player2__last_name']