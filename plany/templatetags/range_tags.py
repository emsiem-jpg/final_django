from django import template

register = template.Library()

@register.filter
def to_range(start, end):
    """Zwraca zakres liczb od `start` do `end` włącznie."""
    return range(int(start), int(end) + 1)
