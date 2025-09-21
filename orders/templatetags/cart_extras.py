from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiply two numbers in templates."""
    try:
        return float(value) * int(arg)
    except Exception:
        return 0
