from django.contrib import admin
from .models import Player, Group, Team, Match

class PlayerAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name')
    search_fields = ['last_name', 'first_name']

class TeamAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'player1', 'player2', 'group', 'rank')
    list_filter = ('group',)
    search_fields = ['player1__first_name', 'player2__first_name']

class MatchAdmin(admin.ModelAdmin):
    list_display = ('team1', 'team2', 'get_score', 'date_played')
    list_filter = ('date_played', 'team1__group')

admin.site.register(Player, PlayerAdmin)
admin.site.register(Group)
admin.site.register(Team, TeamAdmin)
admin.site.register(Match, MatchAdmin)