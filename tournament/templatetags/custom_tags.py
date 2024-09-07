from django import template
from django.template.loader import render_to_string

register = template.Library()

@register.simple_tag
def team_name(team, index):
    return render_to_string('components/team_name.html', {'player1': team.player1, 'player2': team.player2, 'index': index})