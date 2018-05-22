from django import template
from collections import namedtuple

register = template.Library()

MenuPosition = namedtuple('MenuPosition', ('link', 'name'))

@register.simple_tag
def menu_items():
    return (
        MenuPosition('list_statements', 'Statements'),
        MenuPosition('list_accounts', 'Accounts'),
        MenuPosition('list_groups', 'Groups'),
        MenuPosition('list_transactions', 'Transactions'),
    )
