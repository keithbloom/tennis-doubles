from django import template
from django.template.loader import render_to_string

register = template.Library()

@register.simple_tag
def team_name(team, index, group_count, total_teams):
    
    return render_to_string('components/team_name.html', {'player1': team.player1, 'player2': team.player2, 'index': index, 'group_index': group_count})

@register.simple_tag
def header():
    return render_to_string('components/header.html')

@register.simple_tag
def section_tabs(tabs):
    return render_to_string('components/section_tabs.html', {'tabs': tabs})

@register.filter
def get_item(list_or_dict, index):
    """
    Gets an item from a list by index or from a dict by key
    Example usage: {{ mylist|get_item:index }}
    """
    if isinstance(list_or_dict, list) and 0 <= index < len(list_or_dict):
        return list_or_dict[index]
    elif isinstance(list_or_dict, dict):
        return list_or_dict.get(index)
    return None

@register.filter
def sub(a,b):
    return a - b