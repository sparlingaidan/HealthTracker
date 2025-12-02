from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css):
    """Render a BoundField with an extra CSS class.

    Usage: {{ form.field|add_class:"form-control" }}
    """
    try:
        return field.as_widget(attrs={'class': css})
    except Exception:
        return field
