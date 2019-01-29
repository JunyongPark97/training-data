from django import template

register = template.Library()


@register.filter
def filter_char(value):
    content = value.filter(box_type=0)
    return content

@register.filter
def filter_word(value):
    content = value.filter(box_type=1)
    return content