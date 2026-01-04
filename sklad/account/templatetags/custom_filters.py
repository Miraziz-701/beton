from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def space_separate(value):
    try:
        return f"{int(value):,}".replace(",", " ")
    except (ValueError, TypeError):
        return value
    

@register.filter
def dict_get(d, key):
    if isinstance(d, dict):
        return d.get(key, '')
    return ''