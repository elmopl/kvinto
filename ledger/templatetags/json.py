from django import template
from collections import namedtuple
import json

register = template.Library()

@register.filter
def dump_json(data):
    return json.dumps(data)
