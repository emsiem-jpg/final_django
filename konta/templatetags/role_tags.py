from django import template

register = template.Library()

@register.filter
def is_in(value, arg_string):
    """
    Przykład: user.role|is_in:"admin,moderator"
    """
    if not value:
        return False
    allowed = [r.strip() for r in arg_string.split(",")]
    return value in allowed
