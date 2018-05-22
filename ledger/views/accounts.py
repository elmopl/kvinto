from ..models import Account
from django.shortcuts import render
from django.http import JsonResponse
import json

def accounts_list(request):
    accounts = Account.objects.prefetch_related('statements')
    context = {
        'accounts': accounts,
    }
    return render(request, 'accounts.html', context)

def accounts_match(request):
    query = json.loads(request.body)
    
    accounts = Account.objects.prefetch_related('statements')
    if query.get('name'):
       accounts = accounts.filter(name__contains=query['name'])
    if query.get('ids'):
       accounts = accounts.filter(ids__in=query['ids'])

    return JsonResponse({
        'matches': [
            {
                'id': acc.id,
                'name': acc.name,
                'owner': acc.owner.name,
                'currency': acc.currency,
            }
            for acc in accounts
        ]
    })
