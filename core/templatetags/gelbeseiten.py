import names
import random

from django import template

register = template.Library()

@register.simple_tag
def get_random_name():
    return names.get_first_name(gender='female')

@register.simple_tag
def get_random_extension():
    return random.randint(1000,9999)

@register.simple_tag
def is_ad():
    return "ad" if random.uniform(0.0, 1.0) <= 0.01 else ""

@register.simple_tag
def random_icon():
    icons = [
        'aperture',
        'basket',
        'bar-chart',
        'bar-chart',
        'book',
        'bug',
        'briefcase',
        'bullhorn',
        'camera-slr',
        'cart',
        'cart',
        'chat',
        'clipboard',
        'clock',
        'cloud',
        'cog',
        'command',
        'dollar',
        'droplet',
        'envelope-closed',
        'eyedropper',
        'euro',
        'eye',
        'fork',
        'globe',
        'graph',
        'headphones',
        'heart',
        'home',
        'image',
        'infinity',
        'info',
        'key',
        'location',
        'map',
        'map-marker',
        'microphone',
        'monitor',
        'moon',
        'musical-note',
        'paperclip',
        'pencil',
        'people',
        'person',
        'phone',
        'pie-chart',
        'pin',
        'print',
        'pulse',
        'puzzle-piece',
        'rain',
        'script',
        'shield',
        'signal',
        'signpost',
        'star',
        'sun',
        'tablet',
        'tag',
        'tags',
        'target',
        'terminal',
        'video',
        'wrench',
        'yen',
        ]
    return random.choice(icons)