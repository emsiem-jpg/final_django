from django import template

register = template.Library()

@register.filter
def to_range(start, end):
    """
    Django template filter that returns a range of integers from `start` to `end` (inclusive).

    Useful for generating dynamic loops in templates, e.g. for day selection.

    Example usage in template:
        {% for i in 1|to_range:5 %}
            Day {{ i }}
        {% endfor %}

    Args:
        start (int or str): The starting integer of the range.
        end (int or str): The ending integer of the range.

    Returns:
        range: A Python range object from start to end inclusive.
    """
    return range(int(start), int(end) + 1)