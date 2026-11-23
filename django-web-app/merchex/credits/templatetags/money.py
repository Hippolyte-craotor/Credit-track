from django import template

register = template.Library()


@register.filter
def fcfa(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return "0 FCFA"
    formatted = f"{value:,}".replace(",", " ")
    return f"{formatted} FCFA"
