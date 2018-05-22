from django import template
from datetime import date
from datetime import timedelta

register = template.Library()

@register.simple_tag
def relative_date(years=None):
    now = date.today()
    now = now.replace(year = now.year + years)
    return now
