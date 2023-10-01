import textwrap

from django import template

register = template.Library()

@register.filter(name='tokenformat')
def tokenformat(value, blocksize=4):
    return "-".join(textwrap.wrap(value, blocksize))
