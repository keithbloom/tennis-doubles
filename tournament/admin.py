from django.contrib import admin
from django import forms
from .models import Tournament, Group, TournamentGroup, Player, Team, Match

class TournamentGroupInline(admin.TabularInline):
    model = TournamentGroup
    extra = 5
    min_num = 2
    max_num = 5
    validate_min = True
    validate_max = True

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "group":
            kwargs["queryset"] = Group.objects.all().order_by('name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'status']
    list_filter = ['status']
    inlines = [TournamentGroupInline]

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name']

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

class MatchAdminForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['tournament', 'team1', 'team2', 'set1_team1', 'set1_team2',
                 'set2_team1', 'set2_team2', 'set3_team1', 'set3_team2',
                 'date_played', 'retired_team']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # For both new instances and edits, get the tournament
        tournament = None
        if self.instance.pk:
            tournament = self.instance.tournament
        elif self.data.get('tournament'):
            try:
                tournament = Tournament.objects.get(pk=self.data.get('tournament'))
            except Tournament.DoesNotExist:
                pass

        # Set the team querysets based on tournament
        if tournament:
            teams = Team.objects.filter(tournament_group__tournament=tournament)
            self.fields['team1'].queryset = teams
            self.fields['team2'].queryset = teams
        else:
            self.fields['team1'].queryset = Team.objects.none()
            self.fields['team2'].queryset = Team.objects.none()

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    form = MatchAdminForm
    list_display = ('__str__', 'tournament', 'date_played', 'get_score', 'retired_team')
    list_filter = ('tournament', 'team1__tournament_group', 'date_played', 'retired_team')

    class Media:
        js = ('js/match_admin.js',)