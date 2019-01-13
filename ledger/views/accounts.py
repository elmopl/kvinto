from ..models import Account
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from operator import and_
from functools import reduce
import json
import shlex

def accounts_list(request):
    accounts = Account.objects.prefetch_related('statements')
    accounts = accounts.order_by('owner__name', 'name')
    context = {
        'accounts': accounts,
    }
    return render(request, 'accounts.html', context)

def account(request, account_id):
    account = Account.objects.get(id=account_id)
    context = {
        'account': account,
    }
    return render(request, 'account.html', context)


def accounts_match(request):
    query = json.loads(request.body)
    
    accounts = Account.objects.prefetch_related('statements', 'owner')
    name = query.get('name')
    if name is not None:
        name_filters = [
            Q(name__contains=part) | Q(owner__name__contains=part)
            for part in shlex.split(name)
        ]
        accounts = accounts.filter(reduce(and_, name_filters))

    ids = query.get('ids')
    if ids is not None:
        accounts = accounts.filter(ids__in=ids)

    return JsonResponse({
        'matches': [
            {
                'id': acc.id,
                'name': acc.full_name,
                'owner': acc.owner.name,
                'currency': acc.currency,
            }
            for acc in accounts
        ]
    })
