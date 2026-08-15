from django import template
from django.template.loader import render_to_string

register = template.Library()

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

GROUP_NAV_SM_COLS_CLASS = {
    2: "sm:grid-cols-2",
    3: "sm:grid-cols-3",
    4: "sm:grid-cols-4",
    5: "sm:grid-cols-5",
    6: "sm:grid-cols-6",
}

@register.filter
def group_nav_sm_cols(group_total):
    """
    Maps the number of tournament groups to the Tailwind class controlling
    how many columns the group nav uses at the `sm` breakpoint.
    """
    return GROUP_NAV_SM_COLS_CLASS.get(group_total, "sm:grid-cols-7")

# Indices whose tab-badge base color is dark enough that text-gray-900 fails
# WCAG contrast against it (checked against the tab-badge palette in
# tailwind.config.js) — those groups need light text instead.
TAB_BADGE_DARK_INDICES = {3, 4}

@register.filter
def tab_badge_text_class(group_index):
    """
    Text color class to use on top of a bg-tab-badge-{{ group_index }}
    background, chosen for contrast against that group's badge color.
    """
    return "text-white" if group_index in TAB_BADGE_DARK_INDICES else "text-gray-900"
